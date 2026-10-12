"""Shape and producer invariants for documents, secrets and aggregate envelopes."""
import json
from itertools import islice
from .validate_report import SCHEMA_PATH, location

SCHEMAS={n:n+'.schema.json' for n in ('documents-0.1','documents-0.2','secrets-0.1','bundle-0.1')}


def validate(response,max_errors):
    from jsonschema import Draft202012Validator
    from referencing import Registry
    from referencing.exceptions import NoSuchResource
    from .validate_report import validate_response
    from .documents import exit_code as doc_code
    from .secrets import exit_code as secret_code
    from .bundle import exit_code as bundle_code
    def deny(uri):raise NoSuchResource(ref=uri)
    version=response['schema_version']
    schema=json.loads((SCHEMA_PATH.parent/SCHEMAS[version]).read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    validator=Draft202012Validator(schema,registry=Registry(retrieve=deny))
    errors=list(islice(({'code':'schema_'+e.validator,'location':location(e.absolute_path)}
                       for e in validator.iter_errors(response)),max_errors+1))
    def error(code,field):errors.append({'code':code,'location':'/'+field})
    def child(value,field):
        if value is not None and not validate_response(value,max_errors)['valid']:error('invalid_child_report',field)
    if not errors:
        if version.startswith('documents-'):
            if response['coverage_complete'] != (not response['coverage_gaps']):error('coverage_mismatch','coverage_complete')
            if response['coverage_complete'] and (response['parts_inspected']==0 or response.get('format')=='unsupported'):error('empty_document_scope','parts_inspected')
            if response['parts_inspected']>response['limits']['parts'] or response['xml_bytes_read']>response['limits']['total_xml_bytes']:error('document_budget_exceeded','limits')
            if len(response['findings'])>response['limits']['findings']:error('finding_budget_exceeded','findings')
            if any(f['asset_id']!=response['asset_id'] for f in response['findings']):error('document_asset_mismatch','findings')
            from .guard import RULES
            severities={rule[0]:rule[2] for rule in RULES};severities.update({'PUB-005':'high','DOC-001':'medium'})
            for f in response['findings']:
                if f['severity']!=severities[f['check_id']] or f['evidence']['kind']!=('identity_metadata' if f['check_id']=='DOC-001' else 'extracted_line'):error('document_rule_mapping_mismatch','findings')
            code=doc_code(response)
        elif version=='secrets-0.1':
            child(response['text_report'],'text_report')
            completed=response['engine']['status']=='completed'
            if completed != (response['engine']['reason'] is None):error('engine_state_mismatch','engine')
            if completed and (response['text_report'] is None or not response['text_report']['coverage_complete']):error('engine_scope_mismatch','text_report')
            if not completed and response['findings']:error('findings_without_completed_engine','findings')
            code=secret_code(response)
        else:
            child(response['text_report'],'text_report');child(response['secrets_report'],'secrets_report')
            for d in response['documents']:child(d,'documents')
            if not response['secrets_requested'] and response['secrets_report'] is not None:error('unexpected_secret_report','secrets_report')
            complete=(not response['coverage_gaps'] and
                      (response['text_report'] is None or response['text_report']['coverage_complete']) and
                      all(d['coverage_complete'] for d in response['documents']) and
                      (not response['secrets_requested'] or (response['secrets_report'] is not None and response['secrets_report']['engine']['status']=='completed')))
            if response['coverage_complete']!=complete:error('coverage_mismatch','coverage_complete')
            if response['text_report'] is None and not response['documents'] and not response['coverage_gaps']:error('empty_bundle_scope','coverage_gaps')
            if response['files_encountered']>response['limits']['max_files'] or response['bytes_read']>response['limits']['max_bytes']:error('bundle_budget_exceeded','limits')
            count=sum(len(d['findings']) for d in response['documents'])+(len(response['text_report']['findings']) if response['text_report'] else 0)+(len(response['secrets_report']['findings']) if response['secrets_report'] else 0)
            if count>response['limits']['max_findings'] or len(response['documents'])>response['limits']['max_documents']:error('bundle_result_budget_exceeded','limits')
            code=bundle_code(response)
    if errors:return {'valid':False,'kind':'invalid','scanner_exit_code':None,'errors':errors[:max_errors],'errors_truncated':len(errors)>max_errors}
    return {'valid':True,'kind':version,'scanner_exit_code':code,'errors':[],'errors_truncated':False}

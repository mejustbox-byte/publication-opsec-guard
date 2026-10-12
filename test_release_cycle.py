import copy
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from publication_opsec_guard.documents import inspect as document_scan, exit_code as document_code, S, CT, XLSX_TYPE
from publication_opsec_guard.bundle import inspect, exit_code
from publication_opsec_guard.validate_report import validate_response


def workbook(path, shared='safe', extras=None, kind=XLSX_TYPE):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',f'<Types xmlns="{CT}"><Override PartName="/xl/workbook.xml" ContentType="{kind}"/></Types>')
        z.writestr('_rels/.rels','<Relationships><Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{S}"><sheets><sheet name="synthetic" state="hidden"/></sheets></workbook>')
        z.writestr('xl/sharedStrings.xml',f'<sst xmlns="{S}"><si>{shared}</si></sst>')
        z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{S}"><sheetData><row><c t="s"><v>0</v></c></row></sheetData></worksheet>')
        for name,value in (extras or {}).items():z.writestr(name,value)

class ReleaseCycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'material';self.root.mkdir()
    def valid(self,r):
        result=validate_response(r)
        self.assertTrue(result['valid'],result)
        return result
    def test_xlsx_clean_and_rich_shared_string(self):
        p=self.root/'book.xlsx';workbook(p)
        self.assertEqual(document_code(document_scan(p)),0)
        self.valid(document_scan(p))
        workbook(p,shared='<r><t>10.1.</t></r><r><t>2.3</t></r>')
        r=document_scan(p);self.assertEqual(document_code(r),1)
        self.assertEqual(r['findings'][0]['check_id'],'PUB-001')
        self.valid(r)
    def test_xlsx_inline_formula_comment_author(self):
        p=self.root/'book.xlsx';workbook(p,extras={
          'xl/worksheets/sheet2.xml':f'<worksheet xmlns="{S}"><c t="inlineStr"><is><t>host.internal</t></is><f>"10.2.3.4"</f></c></worksheet>',
          'xl/comments1.xml':f'<comments xmlns="{S}"><authors><author>AUTHOR_SENTINEL</author></authors></comments>'})
        r=document_scan(p);self.assertEqual({f['check_id'] for f in r['findings']},{'DOC-001','PUB-001','PUB-002'})
        self.assertNotIn('AUTHOR_SENTINEL',json.dumps(r));self.valid(r)
    def test_xlsx_embeddings_and_macros(self):
        p=self.root/'book.xlsx';workbook(p,extras={'xl/embeddings/object.bin':b'unknown'})
        self.assertEqual(document_code(document_scan(p)),2)
        workbook(p,kind='application/vnd.ms-excel.sheet.macroEnabled.main+xml')
        self.assertEqual(document_code(document_scan(p)),2)
    def test_bundle_mixed_and_document_only(self):
        from test_documents import package
        from test_presentations import presentation
        (self.root/'readme.md').write_text('safe')
        package(self.root/'document.docx');presentation(self.root/'slides.pptx');workbook(self.root/'book.xlsx')
        r=inspect(self.root);self.assertEqual(exit_code(r),0);self.assertEqual(len(r['documents']),3);self.valid(r)
        (self.root/'readme.md').unlink();r=inspect(self.root)
        self.assertIsNone(r['text_report']);self.assertEqual(exit_code(r),0);self.valid(r)
    def test_bundle_unsupported_empty_and_symlink(self):
        self.assertEqual(exit_code(inspect(self.root)),2);self.valid(inspect(self.root))
        (self.root/'file.pdf').write_bytes(b'unsupported');r=inspect(self.root);self.assertEqual(exit_code(r),2);self.valid(r)
        (self.root/'link.txt').symlink_to(self.root/'file.pdf');self.assertEqual(exit_code(inspect(self.root)),2)
    def test_bundle_findings_and_requested_engine_failure(self):
        (self.root/'sample.txt').write_text('10.1.2.3')
        r=inspect(self.root,binary=str(self.base/'missing'),digest='0'*64)
        self.assertEqual(exit_code(r),1);self.assertFalse(r['coverage_complete']);self.valid(r)
        (self.root/'sample.txt').write_text('safe')
        r=inspect(self.root,binary=str(self.base/'missing'),digest='0'*64)
        self.assertEqual(exit_code(r),2);self.valid(r)
    def test_bundle_requested_secrets_do_not_hide_document_gap(self):
        from test_documents import package
        package(self.root/'doc.docx')
        r=inspect(self.root,binary=str(self.base/'missing'),digest='0'*64)
        self.assertEqual(exit_code(r),2)
        self.assertIn('document_secret_engine_not_tested',[g['reason'] for g in r['coverage_gaps']]);self.valid(r)
    def test_bundle_limits(self):
        (self.root/'a.txt').write_text('safe');(self.root/'b.txt').write_text('safe')
        for field,value in [('MAX_FILES',1),('MAX_BYTES',1),('MAX_DIRECTORIES',1)]:
            if field=='MAX_DIRECTORIES':(self.root/'child').mkdir(exist_ok=True)
            with patch('publication_opsec_guard.bundle.'+field,value):
                r=inspect(self.root);self.assertEqual(exit_code(r),2);self.valid(r)
    def test_extended_validation_document_consistency(self):
        p=self.root/'book.xlsx';workbook(p);r=document_scan(p)
        for field,value in [('coverage_complete',False),('parts_inspected',0),('xml_bytes_read',16000001)]:
            bad=copy.deepcopy(r);bad[field]=value;self.assertFalse(validate_response(bad)['valid'])
    def test_extended_validation_bundle_children_and_budget(self):
        (self.root/'a.txt').write_text('safe');r=inspect(self.root);self.valid(r)
        for field,value in [('coverage_complete',False),('bytes_read',50000001),('secrets_requested',True)]:
            bad=copy.deepcopy(r);bad[field]=value;self.assertFalse(validate_response(bad)['valid'])
        bad=copy.deepcopy(r);bad['text_report']['coverage_complete']=False
        self.assertFalse(validate_response(bad)['valid'])
    def test_extended_validation_no_raw_diagnostics(self):
        p=self.root/'book.xlsx';workbook(p);r=document_scan(p)
        r['SECRET_FIELD']='SECRET_VALUE';v=validate_response(r)
        self.assertFalse(v['valid']);self.assertNotIn('SECRET',json.dumps(v))
    def test_extended_validation_secret_state(self):
        (self.root/'a.txt').write_text('safe');r=inspect(self.root,binary=str(self.base/'missing'),digest='0'*64)['secrets_report']
        self.valid(r);r['engine']['status']='completed';r['engine']['reason']=None
        self.valid(r) # shape does not authenticate engine provenance
        r['text_report']=None;self.assertFalse(validate_response(r)['valid'])

    def test_validator_cli_all_extended_envelopes(self):
        p=self.root/'book.xlsx';workbook(p)
        document=document_scan(p)
        legacy=copy.deepcopy(document);legacy.pop('format');legacy['schema_version']='documents-0.1'
        legacy['scope']='docx-utf8-xml-text-and-selected-identity-metadata'
        legacy['asset_id']='historic.docx'
        (self.root/'a.txt').write_text('safe')
        bundle=inspect(self.root)
        secrets=inspect(self.root,binary=str(self.base/'missing'),digest='0'*64)['secrets_report']
        for report, expected in [(document,0),(legacy,0),(bundle,0),(secrets,2),({'schema_version':'unknown'},3)]:
            output=self.base/'saved.json';output.write_text(json.dumps(report),encoding='utf-8')
            result=subprocess.run([sys.executable,'-m','publication_opsec_guard.validate_report',str(output)],
                                  capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,expected,result.stderr+result.stdout)

if __name__=='__main__':unittest.main()

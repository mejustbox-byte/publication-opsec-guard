"""Validate Guard contract 0.2 locally; exit 0/1/2 for valid results, 3 otherwise."""
import argparse
from itertools import islice
import json
import os
from pathlib import Path
import stat
import sys

try:
    from publication_opsec_guard_schemas import __file__ as schema_module_path
except ModuleNotFoundError:
    SCHEMA_PATH = Path(__file__).parent.parent / 'schemas' / 'response-0.2.schema.json'
else:
    SCHEMA_PATH = Path(schema_module_path).with_name('response-0.2.schema.json')
DEFAULT_MAX_BYTES = 16_000_000
DEFAULT_MAX_ERRORS = 32
MAX_JSON_DEPTH = 64
STOP_REASONS = {'file_count_limit', 'total_bytes_limit', 'finding_count_limit',
                'directory_count_limit'}
SAFE_FIELDS = {'schema_version', 'tool_version', 'scope', 'coverage_complete',
               'files_inspected', 'files_encountered', 'bytes_read', 'scan_stopped',
               'limits', 'max_bytes', 'max_files', 'max_total_bytes', 'max_findings',
               'max_directories', 'exclusions', 'findings', 'coverage_gaps',
               'asset_id', 'reason', 'check_id', 'status', 'severity', 'evidence',
               'line', 'redacted', 'remediation', 'error'}


def invalid(code):
    return {'valid': False, 'kind': 'invalid', 'scanner_exit_code': None,
            'errors': [{'code': code, 'location': ''}], 'errors_truncated': False}


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate key')
        result[key] = value
    return result


def reject_constant(_value):
    raise ValueError('Non-JSON number')


def check_json_depth(text):
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == chr(92):
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '{[':
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValueError('JSON depth limit')
        elif char in '}]':
            depth -= 1


def load_response(path, max_bytes=DEFAULT_MAX_BYTES):
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError('Invalid byte limit')
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Symlink input')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Not a regular file')
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('Report byte limit')
    text = raw.decode('utf-8')
    check_json_depth(text)
    return json.loads(text, object_pairs_hook=strict_object,
                      parse_constant=reject_constant)


def local_validator():
    from jsonschema import Draft202012Validator
    from referencing import Registry
    from referencing.exceptions import NoSuchResource

    def deny_retrieval(uri):
        raise NoSuchResource(ref=uri)

    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    # The bundled schema uses only fragment references; deny all remote retrieval.
    return Draft202012Validator(schema, registry=Registry(retrieve=deny_retrieval))


def location(path):
    # Never echo input values, unexpected property names, or source asset paths.
    parts = (str(part) if type(part) is int else part if part in SAFE_FIELDS else '?'
             for part in path)
    return ''.join('/' + part for part in parts)


def consistency_errors(report):
    def error(code, field):
        return {'code': code, 'location': '/' + field}

    gaps = report['coverage_gaps']
    reasons = [gap['reason'] for gap in gaps]
    if report['coverage_complete'] != (not gaps and not report['exclusions']):
        yield error('coverage_mismatch', 'coverage_complete')
    empty_count = reasons.count('empty_scope')
    if empty_count != (1 if report['files_inspected'] == 0 else 0):
        yield error('empty_scope_mismatch', 'coverage_gaps')
    stops = sum(reason in STOP_REASONS for reason in reasons)
    if report['scan_stopped'] != bool(stops) or stops > 1:
        yield error('stop_state_mismatch', 'scan_stopped')
    if report['files_inspected'] > report['files_encountered']:
        yield error('file_counter_mismatch', 'files_inspected')
    if report['files_encountered'] > report['limits']['max_files']:
        yield error('file_budget_exceeded', 'files_encountered')
    if report['bytes_read'] > report['limits']['max_total_bytes']:
        yield error('byte_budget_exceeded', 'bytes_read')
    if len(report['findings']) > report['limits']['max_findings']:
        yield error('finding_budget_exceeded', 'findings')
    if 'finding_count_limit' in reasons and len(report['findings']) != report['limits']['max_findings']:
        yield error('finding_limit_mismatch', 'findings')
    if report['findings'] and (not report['files_inspected'] or not report['bytes_read']):
        yield error('finding_without_input', 'findings')
    if 'file_count_limit' in reasons and report['files_encountered'] != report['limits']['max_files']:
        yield error('file_limit_mismatch', 'files_encountered')
    # A filename is an opaque label, never a path to reopen on the consumer host.


def validate_response(response, max_errors=DEFAULT_MAX_ERRORS):
    """Validate a decoded JSON object; file loading separately enforces strict JSON."""
    if type(max_errors) is not int or max_errors < 1:
        raise ValueError('Invalid error limit')
    if isinstance(response, dict) and response.get('schema_version') in ('documents-0.1', 'documents-0.2', 'secrets-0.1', 'bundle-0.1'):
        from .extended_validation import validate
        return validate(response, max_errors)
    validator = local_validator()
    # Choose a branch for useful safe locations; mixed/unknown envelopes fail closed.
    branch = 'startup_error' if isinstance(response, dict) and 'error' in response else 'report'
    validator = validator.evolve(schema={**validator.schema, 'oneOf': [
        {'$ref': '#/$defs/' + branch}]})
    def shape_errors():
        for outer in validator.iter_errors(response):
            # Unwrap only the envelope oneOf. Finding/gap errors stay concise.
            children = outer.context if outer.validator == 'oneOf' and not outer.path else [outer]
            for item in children:
                yield {'code': 'schema_' + str(item.validator),
                       'location': location(item.absolute_path)}
    errors = list(islice(shape_errors(), max_errors + 1))
    if not errors and branch == 'report':
        errors = list(islice(consistency_errors(response), max_errors + 1))
    if errors:
        return {'valid': False, 'kind': 'invalid', 'scanner_exit_code': None,
                'errors': errors[:max_errors], 'errors_truncated': len(errors) > max_errors}
    code = 2 if branch == 'startup_error' else (
        1 if response['findings'] else 2 if not response['coverage_complete'] else 0)
    return {'valid': True, 'kind': branch, 'scanner_exit_code': code,
            'errors': [], 'errors_truncated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--max-report-bytes', type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument('--max-errors', type=int, default=DEFAULT_MAX_ERRORS)
    args = parser.parse_args()
    try:
        if args.max_errors < 1:
            raise ValueError('Invalid error limit')
        response = load_response(args.report, args.max_report_bytes)
    except (OSError, ValueError, RecursionError, OverflowError):
        result = invalid('input_error')
    else:
        try:
            result = validate_response(response, args.max_errors)
        except ImportError:
            result = invalid('dependency_missing')
        except Exception:
            # Schema/runtime failures must not disclose exception text or succeed.
            result = invalid('validation_unavailable')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return result['scanner_exit_code'] if result['valid'] else 3


if __name__ == '__main__':
    sys.exit(main())

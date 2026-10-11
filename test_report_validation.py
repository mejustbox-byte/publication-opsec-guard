import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from guard import scan
from validate_report import load_response, local_validator, validate_response

ROOT = Path(__file__).parent


class ReportValidationTests(unittest.TestCase):
    def setUp(self):
        self.clean = json.loads((ROOT / 'examples/reports/valid/clean.json').read_text())

    def assert_invalid(self, response, code=None):
        result = validate_response(response)
        self.assertFalse(result['valid'])
        self.assertIsNone(result['scanner_exit_code'])
        if code:
            self.assertIn(code, [e['code'] for e in result['errors']])
        return result

    def test_schema_and_labeled_fixtures(self):
        validator = local_validator()  # Includes Draft202012Validator.check_schema.
        manifest = json.loads((ROOT / 'examples/reports/manifest.json').read_text())
        for case in manifest['cases']:
            with self.subTest(case=case['path']):
                report = json.loads((ROOT / 'examples/reports' / case['path']).read_text())
                result = validate_response(report)
                self.assertEqual(result['valid'], case['valid'])
                self.assertEqual(result['scanner_exit_code'], case['scanner_exit_code'])
                if case['valid']:
                    self.assertTrue(validator.is_valid(report))

    def test_live_scanner_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(validate_response(scan(root))['scanner_exit_code'], 2)
            (root / '.env').write_text('10.1.2.3\n', encoding='utf-8')
            self.assertEqual(validate_response(scan(root))['scanner_exit_code'], 1)
            (root / '.env').write_text('safe', encoding='utf-8')
            self.assertEqual(validate_response(scan(root))['scanner_exit_code'], 0)
            (root / 'second.txt').write_text('safe', encoding='utf-8')
            for limits in ({'max_files': 1}, {'max_bytes': 1}, {'max_total_bytes': 5}):
                self.assertTrue(validate_response(scan(root, **limits))['valid'])
            (root / 'second.txt').write_bytes(b'\x00')
            self.assertTrue(validate_response(scan(root))['valid'])
            (root / 'second.txt').write_bytes(b'\xff')
            self.assertTrue(validate_response(scan(root))['valid'])
            (root / 'child').mkdir()
            self.assertTrue(validate_response(scan(root, max_directories=1))['valid'])

    def test_required_fields_and_unknown_envelopes(self):
        for field in self.clean:
            with self.subTest(field=field):
                report = copy.deepcopy(self.clean)
                del report[field]
                self.assert_invalid(report)
        for report in (None, [], {}, {'status': 'pass'},
                       {'error': 'Invalid input or policy', 'status': 'not_tested', 'findings': []}):
            self.assert_invalid(report)

    def test_schema_types_and_unknown_fields(self):
        for field, value in (('files_inspected', True), ('bytes_read', -1),
                             ('findings', {}), ('scan_stopped', 0), ('scope', 'all-formats'),
                             ('schema_version', '0.1'), ('tool_version', '')):
            with self.subTest(field=field):
                report = copy.deepcopy(self.clean)
                report[field] = value
                self.assert_invalid(report)
        report = copy.deepcopy(self.clean)
        report['limits']['max_files'] = 0
        self.assert_invalid(report)
        report = copy.deepcopy(self.clean)
        report['SECRET_UNEXPECTED_FIELD'] = 'SECRET_UNEXPECTED_VALUE'
        result = self.assert_invalid(report)
        self.assertNotIn('SECRET_UNEXPECTED', json.dumps(result))

    def test_finding_shape_redaction_and_static_rule_mapping(self):
        original = json.loads((ROOT / 'examples/reports/valid/findings.json').read_text())
        for field, value in (('check_id', 'PUB-999'), ('status', 'pass'),
                             ('severity', 'critical'), ('remediation', 'arbitrary')):
            with self.subTest(field=field):
                report = copy.deepcopy(original)
                report['findings'][0][field] = value
                self.assert_invalid(report)
        for evidence in ({'line': 0, 'redacted': True}, {'line': 1, 'redacted': False},
                         {'line': 1, 'redacted': True, 'raw': 'SECRET_EVIDENCE'}):
            report = copy.deepcopy(original)
            report['findings'][0]['evidence'] = evidence
            self.assertNotIn('SECRET_EVIDENCE', json.dumps(self.assert_invalid(report)))

    def test_gap_assets_and_unknown_reasons(self):
        base = copy.deepcopy(self.clean)
        base['coverage_complete'] = False
        for gap in ({'status': 'not_tested', 'reason': 'unknown'},
                    {'status': 'not_tested', 'reason': 'unsupported_format'},
                    {'status': 'not_tested', 'reason': 'empty_scope', 'asset_id': 'wrong'}):
            base['coverage_gaps'] = [gap]
            self.assert_invalid(base)

    def test_coverage_and_empty_scope_consistency(self):
        report = copy.deepcopy(self.clean)
        report['coverage_complete'] = False
        self.assert_invalid(report, 'coverage_mismatch')
        report = copy.deepcopy(self.clean)
        report['files_inspected'] = 0
        self.assert_invalid(report, 'empty_scope_mismatch')
        report['coverage_complete'] = False
        report['coverage_gaps'] = [{'status': 'not_tested', 'reason': 'empty_scope'}] * 2
        self.assert_invalid(report, 'empty_scope_mismatch')

    def test_stop_state_consistency(self):
        report = copy.deepcopy(self.clean)
        report['scan_stopped'] = True
        self.assert_invalid(report, 'stop_state_mismatch')
        original = json.loads((ROOT / 'examples/reports/valid/stopped-bytes.json').read_text())
        report = copy.deepcopy(original)
        report['scan_stopped'] = False
        self.assert_invalid(report, 'stop_state_mismatch')
        report = copy.deepcopy(original)
        report['coverage_gaps'].append({'status': 'not_tested', 'reason': 'directory_count_limit'})
        self.assert_invalid(report, 'stop_state_mismatch')

    def test_budget_and_counter_consistency(self):
        for field, value, code in (('files_inspected', 2, 'file_counter_mismatch'),
                                   ('files_encountered', 10001, 'file_budget_exceeded'),
                                   ('bytes_read', 50000001, 'byte_budget_exceeded')):
            report = copy.deepcopy(self.clean)
            report[field] = value
            self.assert_invalid(report, code)
        report = json.loads((ROOT / 'examples/reports/valid/findings.json').read_text())
        report['limits']['max_findings'] = 1
        self.assert_invalid(report, 'finding_budget_exceeded')
        report['files_inspected'] = 0
        self.assert_invalid(report, 'finding_without_input')
        report = json.loads((ROOT / 'examples/reports/valid/stopped-findings.json').read_text())
        report['limits']['max_findings'] = 2
        self.assert_invalid(report, 'finding_limit_mismatch')
        report = copy.deepcopy(self.clean)
        report.update(coverage_complete=False, scan_stopped=True,
                      coverage_gaps=[{'status': 'not_tested', 'reason': 'file_count_limit'}])
        self.assert_invalid(report, 'file_limit_mismatch')

    def test_error_cap_and_numeric_integer_semantics(self):
        report = copy.deepcopy(self.clean)
        report['files_inspected'] = 1.0  # JSON Schema integer includes zero-fraction numbers.
        self.assertTrue(validate_response(report)['valid'])
        result = validate_response({}, max_errors=1)
        self.assertEqual(len(result['errors']), 1)
        self.assertTrue(result['errors_truncated'])
        for cap in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                validate_response(self.clean, cap)

    def test_strict_json_and_read_boundaries(self):
        raw = json.dumps(self.clean).encode('utf-8')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, 'report.json')
            path.write_bytes(raw)
            self.assertEqual(load_response(path, len(raw)), self.clean)
            with self.assertRaises(ValueError):
                load_response(path, len(raw) - 1)
            for payload in (b'{"x":1,"x":2}', b'{"nested":{"x":1,"x":2}}',
                            b'{"x":NaN}', b'{"x":Infinity}', b'\xff', b'{',
                            b'{} {}', b'\xef\xbb\xbf{}'):
                path.write_bytes(payload)
                with self.assertRaises(ValueError):
                    load_response(path)
            path.write_text('[[' * 1200 + ']]' * 1200)
            with self.assertRaises(ValueError):
                load_response(path)
            path.write_text('[' * 64 + ']' * 64)
            self.assertIsInstance(load_response(path), list)
            path.write_text(json.dumps({'value': '[]{}' * 100}))
            self.assertEqual(load_response(path)['value'], '[]{}' * 100)
            for cap in (0, -1, True):
                with self.assertRaises(ValueError):
                    load_response(path, cap)

    def test_symlink_and_special_file_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'real.json').write_text('{}')
            (root / 'link.json').symlink_to(root / 'real.json')
            with self.assertRaises(ValueError):
                load_response(root / 'link.json')
            if hasattr(os, 'mkfifo'):
                os.mkfifo(root / 'fifo.json')
                with self.assertRaises(ValueError):
                    load_response(root / 'fifo.json')

    def test_no_network_during_validation(self):
        with patch('socket.socket', side_effect=AssertionError('Network attempt')):
            self.assertTrue(validate_response(self.clean)['valid'])

    def test_cli_result_codes_and_safe_errors(self):
        def invoke(path, *args, isolated=False):
            command = [sys.executable]
            if isolated:
                command.append('-S')  # Disable site-packages: optional dependency absent.
            return subprocess.run([*command, str(ROOT / 'validate_report.py'), str(path), *args],
                                  capture_output=True, text=True, timeout=20)
        for name, expected in (('clean', 0), ('findings', 1), ('empty', 2), ('startup-error', 2)):
            with self.subTest(name=name):
                out = invoke(ROOT / 'examples/reports/valid' / (name + '.json'))
                self.assertEqual(out.returncode, expected, out.stderr)
                self.assertTrue(json.loads(out.stdout)['valid'])
        for name in ('false-clean', 'raw-evidence', 'unknown-field'):
            out = invoke(ROOT / 'examples/reports/invalid' / (name + '.json'))
            self.assertEqual(out.returncode, 3)
            self.assertFalse(json.loads(out.stdout)['valid'])
        clean = ROOT / 'examples/reports/valid/clean.json'
        for args in (('--max-report-bytes', '1'), ('--max-errors', '0'),
                     ('--max-report-bytes', '0')):
            self.assertEqual(invoke(clean, *args).returncode, 3)
        out = invoke(clean, isolated=True)
        self.assertEqual(out.returncode, 3)
        self.assertEqual(json.loads(out.stdout)['errors'][0]['code'], 'dependency_missing')
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp, 'SECRET_REPORT_FILENAME.json')
            report.write_text('{"SECRET_KEY":NaN}')
            out = invoke(report)
            self.assertEqual(out.returncode, 3)
            self.assertNotIn('SECRET', out.stdout + out.stderr)
            report.write_text('[[' * 1200 + ']]' * 1200)
            self.assertEqual(invoke(report).returncode, 3)

    def test_unavailable_schema_fails_closed(self):
        from validate_report import main
        import io
        with patch('validate_report.SCHEMA_PATH', ROOT / 'missing-schema.json'), \
                patch('sys.argv', ['validate_report.py', str(ROOT / 'examples/reports/valid/clean.json')]), \
                patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(main(), 3)
            self.assertEqual(json.loads(output.getvalue())['errors'][0]['code'],
                             'validation_unavailable')


if __name__ == '__main__':
    unittest.main()

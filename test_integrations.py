import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parent

class IntegrationTests(unittest.TestCase):
    def invoke(self, root, report, policy='', **kwargs):
        env = dict(os.environ, GUARD_DIRECTORY=str(root), GUARD_REPORT=str(report),
                   GUARD_POLICY=str(policy), GITHUB_OUTPUT=str(report.parent / 'outputs.txt'))
        env.update(kwargs)
        result = subprocess.run([sys.executable, str(ROOT / 'run_integration.py')],
                                env=env, capture_output=True, text=True, timeout=20)
        return result

    def test_clean_findings_and_gap_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); root = base / 'materials'; root.mkdir()
            for i, (text, ext, expected) in enumerate([('safe', '.txt', 0),
                       ('10.1.2.3 SECRET_SYNTHETIC_MARKER', '.txt', 1), ('data', '.bin', 2)]):
                for file in root.iterdir(): file.unlink()
                (root / ('sample' + ext)).write_text(text)
                report = base / f'report{i}.json'
                result = self.invoke(root, report)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertTrue(report.is_file())
                self.assertNotIn('SECRET', result.stdout + result.stderr)
                self.assertIn(f'exit-code={expected}', (base / 'outputs.txt').read_text())
                self.assertIn('coverage_complete', json.loads(report.read_text()))

    def test_invalid_policy_retains_startup_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); root = base / 'materials'; root.mkdir()
            report = base / 'report.json'
            result = self.invoke(root, report, base / 'missing-policy')
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(report.read_text())['status'], 'not_tested')

    def test_report_inside_scope_and_existing_report_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); root = base / 'materials'; root.mkdir()
            report = root / 'report.json'
            self.assertEqual(self.invoke(root, report).returncode, 2)
            self.assertFalse(report.exists())
            report = base / 'existing.json'; report.write_text('original')
            self.assertEqual(self.invoke(root, report).returncode, 2)
            self.assertEqual(report.read_text(), 'original')

    def test_environment_strings_are_literal(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); root = base / '$(touch injected)'; root.mkdir()
            (root / 'sample.txt').write_text('safe')
            result = self.invoke(root, base / 'report.json')
            self.assertEqual(result.returncode, 0)
            self.assertFalse((base / 'injected').exists())

if __name__ == '__main__':
    unittest.main()

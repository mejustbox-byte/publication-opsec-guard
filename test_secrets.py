import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from publication_opsec_guard.secrets import inspect, exit_code, convert

class SecretAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'material'; self.root.mkdir()
        (self.root / 'sample.txt').write_text('safe')
        self.binary = self.base / 'gitleaks'; self.binary.write_bytes(b'synthetic executable')
        self.digest = hashlib.sha256(self.binary.read_bytes()).hexdigest()

    def fake(self, records=None, version='8.24.2', code=None, malformed=False):
        def run(args, **kw):
            if args[1] == 'version':
                kw['stdout'].write(version.encode())
                return subprocess.CompletedProcess(args, 0)
            self.assertIn('--redact=100', args)
            self.assertIn('--ignore-gitleaks-allow', args)
            self.assertEqual(kw['stdout'], subprocess.DEVNULL)
            self.assertEqual(kw['stderr'], subprocess.DEVNULL)
            self.assertFalse(any(k.startswith('GITLEAKS_') for k in kw['env']))
            output = Path(args[args.index('--report-path') + 1])
            rows = [] if records is None else records
            output.write_text('broken' if malformed else json.dumps(rows))
            return subprocess.CompletedProcess(args, code if code is not None else 10 if rows else 0)
        return run

    def execute(self, **kwargs):
        return inspect(self.root, self.binary, self.digest, **kwargs)

    def test_clean_and_redacted_findings(self):
        with patch('subprocess.run', side_effect=self.fake()):
            result = self.execute(); self.assertEqual(exit_code(result), 0)
        rows = [{'RuleID': 'generic-api-key', 'File': 'sample.txt', 'StartLine': 1,
                 'Secret': 'SECRET_SENTINEL', 'Match': 'SECRET_SENTINEL', 'Line': 'SECRET_SENTINEL'}]
        with patch('subprocess.run', side_effect=self.fake(rows)):
            result = self.execute()
        self.assertEqual(exit_code(result), 1)
        self.assertNotIn('SECRET_SENTINEL', json.dumps(result))
        self.assertEqual(result['findings'][0]['asset_id'], 'sample.txt')

    def test_missing_digest_and_version_fail_closed(self):
        with patch('subprocess.run') as engine:
            for binary, digest, reason in [(self.base/'missing', self.digest, 'engine_missing'),
                     (self.binary, '0'*64, 'engine_digest_mismatch'),
                     (self.binary, '', 'invalid_engine_digest')]:
                result = inspect(self.root, binary, digest)
                self.assertEqual(result['engine']['reason'], reason)
                self.assertEqual(exit_code(result), 2)
            engine.assert_not_called()
        with patch('subprocess.run', side_effect=self.fake(version='unknown SECRET')):
            result = self.execute()
            self.assertEqual(result['engine']['reason'], 'engine_version_mismatch')
            self.assertNotIn('SECRET', json.dumps(result))

    def test_timeout_and_engine_error(self):
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('SECRET', 1)):
            result = self.execute()
            self.assertEqual(result['engine']['reason'], 'engine_timeout')
            self.assertNotIn('SECRET', json.dumps(result))
        with patch('subprocess.run', side_effect=self.fake(code=1)):
            self.assertEqual(self.execute()['engine']['reason'], 'engine_failed')

    def test_malformed_inconsistent_and_unsafe_metadata(self):
        for fake in [self.fake(malformed=True), self.fake(code=10), self.fake([
                    {'RuleID':'rule', 'StartLine':1, 'File':'../outside'}]), self.fake([
                    {'RuleID':'SECRET unexpected', 'StartLine':1, 'File':'sample.txt'}])]:
            with patch('subprocess.run', side_effect=fake):
                result = self.execute()
                self.assertEqual(exit_code(result), 2)
                self.assertEqual(result['findings'], [])
                self.assertNotIn('SECRET', json.dumps(result))

    def test_incomplete_scope_never_executes_engine(self):
        (self.root/'image.bin').write_bytes(b'x')
        with patch('subprocess.run') as engine:
            result = self.execute()
            self.assertEqual(result['engine']['reason'], 'incomplete_text_scope')
            self.assertEqual(exit_code(result), 2)
            engine.assert_not_called()

    def test_invalid_policy_and_timeout(self):
        result = self.execute(policy=self.base/'missing')
        self.assertEqual(exit_code(result), 2)
        for timeout in (0, 301, True):
            self.assertEqual(self.execute(timeout=timeout)['engine']['reason'], 'invalid_timeout')

    def test_text_findings_survive_engine_unavailability(self):
        (self.root/'sample.txt').write_text('10.1.2.3')
        result = inspect(self.root, self.base/'missing', self.digest)
        self.assertEqual(exit_code(result), 1)
        self.assertEqual(result['engine']['status'], 'not_tested')

    def test_oversized_report_and_scope_change(self):
        fake = self.fake()
        def oversized(args, **kw):
            out = fake(args, **kw)
            if args[1] == 'dir':
                Path(args[args.index('--report-path')+1]).write_bytes(b'x'*4_000_001)
            return out
        with patch('subprocess.run', side_effect=oversized):
            self.assertEqual(exit_code(self.execute()), 2)
        with patch('publication_opsec_guard.secrets.snapshot_text', return_value=(99, 1)), \
                patch('subprocess.run', side_effect=self.fake()):
            self.assertEqual(self.execute()['engine']['reason'], 'scope_changed')

if __name__ == '__main__':
    unittest.main()

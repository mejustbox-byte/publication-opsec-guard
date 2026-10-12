"""Labeled synthetic rule cases; counts and line numbers are asserted independently."""
import json
from pathlib import Path
import tempfile
import unittest
from guard import scan
from validate_report import validate_response

class RuleCorpusTests(unittest.TestCase):
    def test_labeled_corpus(self):
        cases = json.loads((Path(__file__).parent / 'examples/rules/corpus.json').read_text(encoding='utf-8'))['cases']
        self.assertEqual(len({c['id'] for c in cases}), len(cases))
        self.assertEqual({c['rule'] for c in cases}, {f'PUB-{i:03}' for i in range(1, 6)})
        for case in cases:
            with self.subTest(case=case['id']):
                with tempfile.TemporaryDirectory() as tmp:
                    Path(tmp, 'sample.txt').write_text(case['text'], encoding='utf-8')
                    report = scan(tmp, markers=case['markers'])
                self.assertTrue(report['coverage_complete'])
                self.assertTrue(validate_response(report)['valid'])
                matches = [f for f in report['findings'] if f['check_id'] == case['rule']]
                self.assertEqual(len(matches), case['expected_count'])
                self.assertTrue(all(f['evidence']['redacted'] for f in matches))
                if case['text'].startswith('first\n'):
                    self.assertEqual([f['evidence']['line'] for f in matches], [2, 2])

if __name__ == '__main__':
    unittest.main()

import json
from pathlib import Path
import tempfile
import unittest
from guard import scan

class GuardTests(unittest.TestCase):
 def run_scan(self,text,markers=()):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'sample.md').write_text(text);return scan(tmp,markers)
 def test_all_rules_and_redaction(self):
  r=self.run_scan('10.2.3.4\nserver.internal\n/home/alice/test\n-----BEGIN PRIVATE KEY-----\nSyntheticOrg', ['SyntheticOrg'])
  self.assertEqual({f['check_id'] for f in r['findings']},{'PUB-001','PUB-002','PUB-003','PUB-004','PUB-005'})
  encoded=json.dumps(r)
  for secret in ('10.2.3.4','server.internal','alice','SyntheticOrg'):self.assertNotIn(secret,encoded)
 def test_documentation_ip_and_invalid_ip(self):
  self.assertFalse(self.run_scan('192.0.2.1 198.51.100.2 203.0.113.3 999.1.1.1')['findings'])
 def test_private_range_boundaries(self):
  r=self.run_scan('172.15.0.1 172.16.0.1 172.31.255.255 172.32.0.1 192.168.1.1')
  self.assertEqual(len(r['findings']),3)
 def test_symlink_and_unsupported(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'image.png').write_bytes(b'x');Path(tmp,'link.md').symlink_to('/etc/passwd')
   r=scan(tmp);self.assertFalse(r['coverage_complete']);self.assertEqual(len(r['coverage_gaps']),2)
 def test_size_encoding_and_binary(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'large.md').write_text('abc');Path(tmp,'bad.txt').write_bytes(b'\xff');Path(tmp,'binary.txt').write_bytes(b'\x00')
   r=scan(tmp,max_bytes=2);self.assertEqual(len(r['coverage_gaps']),3)
 def test_file_limit(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'a.txt').write_text('ok');Path(tmp,'b.txt').write_text('ok')
   self.assertEqual(scan(tmp,max_files=1)['coverage_gaps'][0]['reason'],'file_count_limit')
 def test_marker_is_literal(self):
  self.assertEqual(len(self.run_scan('a.b axb',['a.b'])['findings']),1)
 def test_clean(self):
  r=self.run_scan('Example documentation');self.assertTrue(r['coverage_complete']);self.assertFalse(r['findings'])
if __name__=='__main__':unittest.main()

import json
from pathlib import Path
import tempfile
import unittest
from guard import scan, read_policy, validate_markers

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
   r=scan(tmp);self.assertFalse(r['coverage_complete']);self.assertEqual(len(r['coverage_gaps']),3)
 def test_size_encoding_and_binary(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'large.md').write_text('abc');Path(tmp,'bad.txt').write_bytes(b'\xff');Path(tmp,'binary.txt').write_bytes(b'\x00')
   r=scan(tmp,max_bytes=2);self.assertEqual(len(r['coverage_gaps']),4)
 def test_file_limit(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'a.txt').write_text('ok');Path(tmp,'b.txt').write_text('ok')
   self.assertEqual(scan(tmp,max_files=1)['coverage_gaps'][0]['reason'],'file_count_limit')
 def test_marker_is_literal(self):
  self.assertEqual(len(self.run_scan('a.b axb',['a.b'])['findings']),1)
 def test_clean(self):
  r=self.run_scan('Example documentation');self.assertTrue(r['coverage_complete']);self.assertFalse(r['findings'])
class CliTests(unittest.TestCase):
 def test_exit_codes_and_invalid_policy(self):
  import subprocess,sys
  guard=Path(__file__).with_name('guard.py')
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp,'input');directory.mkdir()
   def invoke(*args):
    return subprocess.run([sys.executable,str(guard),str(directory),*args],capture_output=True,text=True)
   Path(directory,'safe.md').write_text('Safe example')
   self.assertEqual(invoke().returncode,0)
   Path(directory,'safe.md').write_text('10.1.2.3')
   self.assertEqual(invoke().returncode,1)
   Path(directory,'safe.md').unlink();Path(directory,'unknown.pdf').write_bytes(b'x')
   self.assertEqual(invoke().returncode,2)
   policy=Path(tmp,'policy.json');policy.write_text('{"markers":[""]}')
   out=invoke('--policy',str(policy));self.assertEqual(out.returncode,2);self.assertEqual(json.loads(out.stdout)['status'],'not_tested')
   self.assertEqual(invoke('--max-bytes','0').returncode,2)

class HardeningTests(unittest.TestCase):
 def test_exact_env(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'.env').write_text('HOST=10.1.2.3')
   r=scan(tmp);self.assertEqual(r['files_inspected'],1);self.assertEqual(r['findings'][0]['check_id'],'PUB-001')
 def test_empty_scope(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=scan(tmp);self.assertFalse(r['coverage_complete']);self.assertEqual(r['coverage_gaps'][0]['reason'],'empty_scope')
 def test_exclusions_visible(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'.git').mkdir();Path(tmp,'safe.txt').write_text('Safe')
   r=scan(tmp);self.assertFalse(r['coverage_complete']);self.assertEqual(r['exclusions'][0]['asset_id'],'.git')
 def test_total_bytes_limit_and_exact_boundary(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'a.txt').write_text('abc');Path(tmp,'b.txt').write_text('def')
   r=scan(tmp,max_total_bytes=5);self.assertEqual(r['bytes_read'],5);self.assertTrue(r['scan_stopped']);self.assertEqual(r['coverage_gaps'][0]['reason'],'total_bytes_limit')
   r=scan(tmp,max_total_bytes=6);self.assertTrue(r['coverage_complete']);self.assertEqual(r['files_inspected'],2)
 def test_invalid_files_consume_byte_budget(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'a.txt').write_bytes(b'\xff');Path(tmp,'b.txt').write_text('abc')
   r=scan(tmp,max_total_bytes=3);self.assertEqual(r['bytes_read'],3);self.assertTrue(r['scan_stopped'])
 def test_finding_limit_and_exact_boundary(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'a.txt').write_text('10.1.2.3 10.1.2.4')
   r=scan(tmp,max_findings=1);self.assertEqual(len(r['findings']),1);self.assertTrue(r['scan_stopped']);self.assertEqual(r['coverage_gaps'][0]['reason'],'finding_count_limit')
   self.assertTrue(scan(tmp,max_findings=2)['coverage_complete'])
 def test_directory_limit(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'child').mkdir();Path(tmp,'child/a.txt').write_text('Safe')
   r=scan(tmp,max_directories=1);self.assertTrue(r['scan_stopped']);self.assertEqual(r['coverage_gaps'][0]['reason'],'directory_count_limit')
 def test_policy_utf8(self):
  with tempfile.TemporaryDirectory() as tmp:
   policy=Path(tmp,'policy.json');policy.write_text('{"markers":["Проект"]}',encoding='utf-8')
   self.assertEqual(read_policy(policy),('Проект',))
   Path(tmp,'a.txt').write_text('ПРОЕКТ',encoding='utf-8')
   # The policy is intentionally also scanned here; substring matches remain expected.
   self.assertTrue(any(f['check_id']=='PUB-005' for f in scan(tmp,read_policy(policy))['findings']))
 def test_policy_unknown_and_duplicate_fields(self):
  for value in ('{"marker":[]}','{"markers":[],"markers":[]}','[]','{"markers":"x"}'):
   with self.subTest(value=value),tempfile.TemporaryDirectory() as tmp:
    policy=Path(tmp,'policy.json');policy.write_text(value)
    with self.assertRaises(ValueError):read_policy(policy)
 def test_policy_limits_and_duplicate_markers(self):
  for markers in (['a','A'],[''],[' '],['x'*257],['x\x00'],['x']*129):
   with self.subTest(markers=markers):
    with self.assertRaises(ValueError):validate_markers(markers)
  with tempfile.TemporaryDirectory() as tmp:
   policy=Path(tmp,'policy.json');policy.write_bytes(b' '*65537)
   with self.assertRaises(ValueError):read_policy(policy)
 def test_positive_integer_api_limits(self):
  with tempfile.TemporaryDirectory() as tmp:
   for value in (0,-1,True,1.5):
    with self.subTest(value=value):
     with self.assertRaises(ValueError):scan(tmp,max_total_bytes=value)
 def test_newline_line_numbers(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'a.txt').write_text('a\nmarker\nmarker')
   r=scan(tmp,['marker']);self.assertEqual([f['evidence']['line'] for f in r['findings']],[2,3])
 def test_cli_empty_unknown_utf8_and_limits(self):
  import subprocess,sys
  guard=Path(__file__).with_name('guard.py')
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp,'input');directory.mkdir();policy=Path(tmp,'policy.json')
   def invoke(*args):return subprocess.run([sys.executable,str(guard),str(directory),*args],capture_output=True,text=True)
   self.assertEqual(invoke().returncode,2)
   Path(directory,'a.txt').write_text('Проект',encoding='utf-8');policy.write_text('{"markers":["Проект"]}',encoding='utf-8')
   self.assertEqual(invoke('--policy',str(policy)).returncode,1)
   policy.write_text('{"marker":[]}');self.assertEqual(invoke('--policy',str(policy)).returncode,2)
   self.assertEqual(invoke('--max-findings','0').returncode,2)
   self.assertEqual(invoke('--max-total-bytes','1').returncode,2)

if __name__=='__main__':unittest.main()

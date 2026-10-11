"""Offline, read-only text publication checks. No raw matches in output."""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import sys

TEXT = {'.txt', '.md', '.rst', '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.csv', '.py', '.ps1', '.sh', '.xml', '.html', '.env'}
RULES = [
 ('PUB-001', re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])'), 'high', 'Replace internal addresses with documentation addresses.'),
 ('PUB-002', re.compile(r'\b[\w.-]+\.(?:local|internal)\b', re.I), 'medium', 'Replace internal domain names with example.invalid.'),
 ('PUB-003', re.compile(r'(?:/Users/|/home/|[A-Za-z]:\\Users\\)[^\s/\\]+'), 'medium', 'Replace identifying user paths with synthetic examples.'),
 ('PUB-004', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----'), 'critical', 'Remove the private key; if exposed, rotate it.'),
]

def private_v4(value):
 ip=ipaddress.ip_address(value)
 return any(ip in ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16'))

def scan(root, markers=(), max_bytes=2_000_000, max_files=10000):
 root=Path(root)
 if root.is_symlink() or not root.is_dir():raise ValueError('Input must be a non-symlink directory')
 root=root.resolve();findings=[];errors=[];inspected=0;seen=0
 # Walk without following symlink directories; no input is modified.
 import os
 for directory, dirs, names in os.walk(root, followlinks=False, onerror=lambda e:errors.append({'status':'not_tested','reason':'directory_unreadable'})):
  dirs.sort();names.sort()
  for name in list(dirs):
   if (Path(directory)/name).is_symlink():
    errors.append({'asset_id':str((Path(directory)/name).relative_to(root)),'status':'not_tested','reason':'symlink'});dirs.remove(name)
  dirs[:]=[d for d in dirs if d not in ('.git','__pycache__')]
  for name in names:
   seen+=1
   if seen>max_files:
    errors.append({'status':'not_tested','reason':'file_count_limit'});return result(findings,errors,inspected)
   path=Path(directory)/name;asset=str(path.relative_to(root))
   reason=None
   if path.is_symlink():reason='symlink'
   elif path.suffix.lower() not in TEXT and path.name not in ('Dockerfile',):reason='unsupported_format'
   if reason:errors.append({'asset_id':asset,'status':'not_tested','reason':reason});continue
   try:
    # O_NOFOLLOW closes the file-symlink race on supporting operating systems.
    flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
    fd=os.open(path,flags)
    with os.fdopen(fd,'rb') as stream:
     import stat
     if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('not_regular_file')
     raw=stream.read(max_bytes+1)
    if len(raw)>max_bytes:raise ValueError('size_limit')
    if b'\x00' in raw:raise ValueError('binary_content')
    content=raw.decode('utf-8')
   except (OSError,ValueError) as exc:
    errors.append({'asset_id':asset,'status':'not_tested','reason':str(exc) if isinstance(exc,ValueError) and not isinstance(exc,UnicodeError) else 'unreadable_or_invalid_utf8'});continue
   inspected+=1
   for cid,pattern,severity,remediation in RULES:
    for match in pattern.finditer(content):
     if cid=='PUB-001':
      try:
       if not private_v4(match.group()):continue
      except ValueError:continue
     findings.append({'check_id':cid,'asset_id':asset,'status':'fail','severity':severity,'evidence':{'line':content.count('\n',0,match.start())+1,'redacted':True},'remediation':remediation})
   for marker in markers:
    for match in re.finditer(re.escape(marker),content,re.I):
     findings.append({'check_id':'PUB-005','asset_id':asset,'status':'fail','severity':'high','evidence':{'line':content.count('\n',0,match.start())+1,'redacted':True},'remediation':'Review and replace the organization marker.'})
 return result(findings,errors,inspected)

def result(findings,errors,inspected):
 return {'schema_version':'0.1','tool_version':'0.1.0a1','scope':'utf8-text-only','coverage_complete':not errors,'files_inspected':inspected,'findings':findings,'coverage_gaps':errors}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory');p.add_argument('--policy',type=Path);p.add_argument('--max-bytes',type=int,default=2_000_000);p.add_argument('--max-files',type=int,default=10000);args=p.parse_args()
 try:
  if args.max_bytes<1 or args.max_files<1:raise ValueError('Limits must be positive')
  policy=json.loads(args.policy.read_text()) if args.policy else {}
  if not isinstance(policy,dict):raise ValueError('Policy must be an object')
  markers=policy.get('markers',[])
  if not isinstance(markers,list) or any(not isinstance(m,str) or not m.strip() for m in markers):raise ValueError('Markers must be nonempty strings')
  report=scan(args.directory,markers,args.max_bytes,args.max_files)
 except (OSError,ValueError):
  print(json.dumps({'error':'Invalid input or policy','status':'not_tested'}));return 2
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return 1 if report['findings'] else (2 if report['coverage_gaps'] else 0)

if __name__=='__main__':sys.exit(main())

"""One bounded publication inspection for text and supported OOXML files."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from .guard import VERSION, TEXT, EXCLUDED, scan, read_policy
from .documents import PROFILES, inspect as document_scan
from .secrets import inspect as secret_scan

MAX_FILES = 1000
MAX_BYTES = 50_000_000
MAX_DIRECTORIES = 1000
MAX_FINDINGS = 10000
MAX_DOCUMENTS = 100


def inspect(directory, policy=None, binary=None, digest=None):
    result = {'schema_version':'bundle-0.1','tool_version':VERSION,
              'scope':'utf8-text-and-supported-ooxml','secrets_requested':bool(binary or digest),
              'coverage_complete':False,'files_encountered':0,'bytes_read':0,
              'limits':{'max_files':MAX_FILES,'max_bytes':MAX_BYTES,'max_directories':MAX_DIRECTORIES,'max_findings':MAX_FINDINGS,'max_documents':MAX_DOCUMENTS},
              'text_report':None,'documents':[],'secrets_report':None,'coverage_gaps':[]}
    def gap(reason, asset=None):
        entry={'status':'not_tested','reason':reason}
        if asset is not None:entry['asset_id']=asset
        result['coverage_gaps'].append(entry)
    try:
        markers=read_policy(policy)
        root=Path(directory)
        if root.is_symlink() or not root.is_dir():raise ValueError('Invalid scope')
        root=root.resolve()
        with tempfile.TemporaryDirectory(prefix='guard-bundle-') as temp:
            base=Path(temp);text=base/'text';text.mkdir();docs=base/'docs';docs.mkdir()
            directories=0;stopped=False;text_count=0
            for current, children, names in os.walk(root,followlinks=False,onerror=lambda _:gap('directory_unreadable')):
                directories+=1
                if directories>MAX_DIRECTORIES or len(children)>MAX_DIRECTORIES-directories:
                    gap('directory_count_limit');break
                children.sort();names.sort()
                for child in list(children):
                    path=Path(current)/child;asset=str(path.relative_to(root))
                    if path.is_symlink() or child in EXCLUDED:
                        gap('excluded_or_symlink_directory',asset);children.remove(child)
                for name in names:
                    if result['files_encountered']>=MAX_FILES:gap('file_count_limit');stopped=True;break
                    result['files_encountered']+=1
                    source=Path(current)/name;asset=str(source.relative_to(root))
                    if source.is_symlink():gap('symlink',asset);continue
                    extension=source.suffix.lower();office=extension in PROFILES
                    supported=extension in TEXT or name in ('Dockerfile','.env')
                    if not office and not supported:gap('unsupported_format',asset);continue
                    if office and len(result['documents'])>=MAX_DOCUMENTS:
                        gap('document_count_limit');stopped=True;break
                    limit=8_000_000 if office else 2_000_000
                    remaining=MAX_BYTES-result['bytes_read']
                    if remaining<=0:gap('total_bytes_limit');stopped=True;break
                    try:
                        fd=os.open(source,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
                        with os.fdopen(fd,'rb') as stream:
                            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):gap('not_regular_file',asset);continue
                            payload=stream.read(min(limit+1,remaining));result['bytes_read']+=len(payload)
                            if os.fstat(stream.fileno()).st_size>remaining:
                                gap('total_bytes_limit',asset);stopped=True;break
                        if len(payload)>limit:gap('file_size_limit',asset);continue
                        destination=(docs if office else text)/asset
                        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(payload)
                        if office:
                            report=document_scan(destination,policy)
                            report['asset_id']=asset
                            for finding in report['findings']:finding['asset_id']=asset
                            if sum(len(d['findings']) for d in result['documents'])+len(report['findings'])>MAX_FINDINGS:
                                gap('finding_count_limit');stopped=True;break
                            result['documents'].append(report)
                        else:text_count+=1
                    except OSError:gap('unreadable',asset)
                if stopped:break
            if text_count:
                remaining_findings=MAX_FINDINGS-sum(len(d['findings']) for d in result['documents'])
                if remaining_findings<1:gap('finding_count_limit')
                else:result['text_report']=scan(text,markers=markers,max_findings=remaining_findings)
            if not text_count and not result['documents']:gap('empty_scope')
            if result['secrets_requested']:
                if not binary or not digest:gap('incomplete_engine_configuration')
                elif text_count:
                    secret_result=secret_scan(text,binary,digest,policy)
                    used=sum(len(d['findings']) for d in result['documents'])+(len(result['text_report']['findings']) if result['text_report'] else 0)
                    if used+len(secret_result['findings'])>MAX_FINDINGS:gap('finding_count_limit')
                    else:result['secrets_report']=secret_result
                else:gap('no_secret_text_scope')
                for report in result['documents']:gap('document_secret_engine_not_tested',report['asset_id'])
            result['coverage_complete']=(not result['coverage_gaps'] and
                (result['text_report'] is None or result['text_report']['coverage_complete']) and
                all(d['coverage_complete'] for d in result['documents']) and
                (not result['secrets_requested'] or (result['secrets_report'] is not None and
                 result['secrets_report']['engine']['status']=='completed')))
    except (OSError,ValueError,RecursionError):gap('invalid_input_or_policy')
    return result


def exit_code(report):
    text=report['text_report'];secrets=report['secrets_report']
    if (text and text['findings']) or any(d['findings'] for d in report['documents']) or (secrets and secrets['findings']):return 1
    return 0 if report['coverage_complete'] else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory');parser.add_argument('--policy')
    parser.add_argument('--gitleaks');parser.add_argument('--engine-sha256')
    args=parser.parse_args()
    result=inspect(args.directory,args.policy,args.gitleaks,args.engine_sha256)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return exit_code(result)

if __name__=='__main__':sys.exit(main())

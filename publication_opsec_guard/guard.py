"""Offline, read-only text publication checks. No raw matches in output."""
import argparse
from bisect import bisect_left
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import sys

VERSION = "0.2.0a3"
SCHEMA_VERSION = "0.2"
TEXT = {'.txt', '.md', '.rst', '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.csv', '.py', '.ps1', '.sh', '.xml', '.html', '.env'}
EXCLUDED = {'.git', '__pycache__'}
PRIVATE_NETS = tuple(ipaddress.ip_network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))
POLICY_BYTES = 65536
MAX_MARKERS = 128
MAX_MARKER_CHARS = 256
RULES = [
    ('PUB-001', re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])'), 'high', 'Replace internal addresses with documentation addresses.'),
    ('PUB-002', re.compile(r'\b[\w.-]+\.(?:local|internal)\b', re.I), 'medium', 'Replace internal domain names with example.invalid.'),
    ('PUB-003', re.compile(r'(?:/Users/|/home/|[A-Za-z]:\\Users\\)[^\s/\\]+'), 'medium', 'Replace identifying user paths with synthetic examples.'),
    ('PUB-004', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----'), 'critical', 'Remove the private key; if exposed, rotate it.'),
]


def private_v4(value):
    ip = ipaddress.ip_address(value)
    return any(ip in network for network in PRIVATE_NETS)


def validate_markers(markers):
    if not isinstance(markers, (list, tuple)) or len(markers) > MAX_MARKERS:
        raise ValueError('Invalid markers')
    seen = set()
    for marker in markers:
        if (not isinstance(marker, str) or not marker.strip()
                or len(marker) > MAX_MARKER_CHARS or '\x00' in marker
                or marker.casefold() in seen):
            raise ValueError('Invalid markers')
        seen.add(marker.casefold())
    return tuple(markers)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate policy field')
        result[key] = value
    return result


def read_policy(path):
    if path is None:
        return ()
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Policy symlink')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Policy must be a regular file')
        payload = stream.read(POLICY_BYTES + 1)
    if len(payload) > POLICY_BYTES:
        raise ValueError('Policy size limit')
    policy = json.loads(payload.decode('utf-8'), object_pairs_hook=unique_object)
    if not isinstance(policy, dict) or set(policy) - {'markers'}:
        raise ValueError('Unknown policy field or invalid object')
    return validate_markers(policy.get('markers', []))


def scan(root, markers=(), max_bytes=2_000_000, max_files=10000,
         max_total_bytes=50_000_000, max_findings=10000, max_directories=10000):
    limits = (max_bytes, max_files, max_total_bytes, max_findings, max_directories)
    if any(type(value) is not int or value < 1 for value in limits):
        raise ValueError('Limits must be positive integers')
    markers = validate_markers(markers)
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Input must be a non-symlink directory')
    root = root.resolve()
    findings, errors, exclusions = [], [], []
    inspected = seen = total_bytes = directories = 0
    stopped = False
    rules = RULES + [('PUB-005', re.compile(re.escape(marker), re.I), 'high',
                      'Review and replace the organization marker.') for marker in markers]

    def gap(reason, asset=None):
        record = {'status': 'not_tested', 'reason': reason}
        if asset is not None:
            record['asset_id'] = asset
        errors.append(record)

    def finish():
        if not inspected and not any(e['reason'] == 'empty_scope' for e in errors):
            gap('empty_scope')
        return {
            'schema_version': SCHEMA_VERSION, 'tool_version': VERSION,
            'scope': 'utf8-text-only', 'coverage_complete': not errors and not exclusions,
            'files_inspected': inspected, 'files_encountered': seen,
            'bytes_read': total_bytes, 'scan_stopped': stopped,
            'limits': dict(zip(('max_bytes', 'max_files', 'max_total_bytes',
                                'max_findings', 'max_directories'), limits)),
            'exclusions': exclusions, 'findings': findings, 'coverage_gaps': errors,
        }

    for directory, dirs, names in os.walk(
            root, followlinks=False, onerror=lambda _error: gap('directory_unreadable')):
        directories += 1
        if directories > max_directories:
            stopped = True
            gap('directory_count_limit')
            return finish()
        dirs.sort()
        names.sort()
        # Reject excessive immediate fanout before recording child paths.
        if len(dirs) > max_directories - directories:
            stopped = True
            gap('directory_count_limit')
            return finish()
        for name in list(dirs):
            path = Path(directory) / name
            asset = str(path.relative_to(root))
            if path.is_symlink():
                gap('symlink', asset)
                dirs.remove(name)
            elif name in EXCLUDED:
                exclusions.append({'asset_id': asset, 'reason': 'excluded_directory'})
                dirs.remove(name)
        for name in names:
            if seen >= max_files:
                stopped = True
                gap('file_count_limit')
                return finish()
            seen += 1
            path = Path(directory) / name
            asset = str(path.relative_to(root))
            if path.is_symlink():
                gap('symlink', asset)
                continue
            if path.suffix.lower() not in TEXT and path.name not in ('Dockerfile', '.env'):
                gap('unsupported_format', asset)
                continue
            remaining = max_total_bytes - total_bytes
            if remaining <= 0:
                stopped = True
                gap('total_bytes_limit', asset)
                return finish()
            try:
                flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
                fd = os.open(path, flags)
                with os.fdopen(fd, 'rb') as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        gap('not_regular_file', asset)
                        continue
                    read_limit = min(max_bytes + 1, remaining)
                    raw = stream.read(read_limit)
                    total_bytes += len(raw)
                    # Stat size plus the bounded read prevents exceeding the byte budget.
                    if os.fstat(stream.fileno()).st_size > remaining:
                        stopped = True
                        gap('total_bytes_limit', asset)
                        return finish()
                if len(raw) > max_bytes:
                    gap('size_limit', asset)
                    continue
                if b'\x00' in raw:
                    gap('binary_content', asset)
                    continue
                content = raw.decode('utf-8')
            except (OSError, UnicodeError):
                gap('unreadable_or_invalid_utf8', asset)
                continue
            inspected += 1
            newlines = [match.start() for match in re.finditer('\n', content)]
            for cid, pattern, severity, remediation in rules:
                for match in pattern.finditer(content):
                    if cid == 'PUB-001':
                        try:
                            if not private_v4(match.group()):
                                continue
                        except ValueError:
                            continue
                    if len(findings) >= max_findings:
                        stopped = True
                        gap('finding_count_limit', asset)
                        return finish()
                    findings.append({
                        'check_id': cid, 'asset_id': asset, 'status': 'fail',
                        'severity': severity,
                        'evidence': {'line': bisect_left(newlines, match.start()) + 1,
                                     'redacted': True},
                        'remediation': remediation,
                    })
    return finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    parser.add_argument('--policy', type=Path)
    for name, default in (('max-bytes', 2_000_000), ('max-files', 10000),
                          ('max-total-bytes', 50_000_000), ('max-findings', 10000),
                          ('max-directories', 10000)):
        parser.add_argument('--' + name, type=int, default=default)
    args = parser.parse_args()
    try:
        report = scan(args.directory, read_policy(args.policy), args.max_bytes,
                      args.max_files, args.max_total_bytes, args.max_findings,
                      args.max_directories)
    except (OSError, ValueError, RecursionError):
        print(json.dumps({'error': 'Invalid input or policy', 'status': 'not_tested'}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report['findings'] else (2 if not report['coverage_complete'] else 0)


if __name__ == '__main__':
    sys.exit(main())

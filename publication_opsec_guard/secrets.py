"""Optional pinned Gitleaks adapter; separate secrets-0.1 response envelope."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from .guard import VERSION, scan, read_policy
from .validate_report import load_response

ENGINE_VERSION = '8.24.2'
MAX_REPORT_BYTES = 4_000_000
MAX_FINDINGS = 10000


def convert(records, snapshot):
    if not isinstance(records, list) or len(records) > MAX_FINDINGS:
        raise ValueError('Invalid findings')
    findings = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Invalid record')
        rule, line, file = record.get('RuleID'), record.get('StartLine'), record.get('File')
        if (not isinstance(rule, str) or not re.fullmatch(r'[a-z0-9-]{1,128}', rule)
                or type(line) is not int or line < 1 or not isinstance(file, str)):
            raise ValueError('Invalid metadata')
        path = Path(file)
        path = path if path.is_absolute() else snapshot / path
        resolved = path.resolve()
        if snapshot not in resolved.parents or not resolved.is_file():
            raise ValueError('Unexpected asset')
        findings.append({'engine_rule': rule, 'asset_id': str(resolved.relative_to(snapshot)),
                         'status': 'fail', 'evidence': {'line': line, 'redacted': True}})
    return findings


def snapshot_text(root, target, limits):
    total = count = 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        for child in dirs:
            if (Path(directory) / child).is_symlink():
                raise ValueError('Changed tree')
        for name in names:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError('Changed tree')
            count += 1
            if count > limits['max_files']:
                raise ValueError('Changed file count')
            flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
            fd = os.open(path, flags)
            with os.fdopen(fd, 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError('Changed file type')
                data = stream.read(limits['max_bytes'] + 1)
            total += len(data)
            if len(data) > limits['max_bytes'] or total > limits['max_total_bytes'] or b'\x00' in data:
                raise ValueError('Changed bytes')
            data.decode('utf-8')
            destination = target / path.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    return count, total


def inspect(directory, binary, digest, policy=None, timeout=30):
    response = {'schema_version': 'secrets-0.1', 'tool_version': VERSION,
                'engine': {'name': 'gitleaks', 'required_version': ENGINE_VERSION,
                           'status': 'not_tested', 'reason': 'invalid_input'},
                'text_report': None, 'findings': []}
    def gap(reason):
        response['engine']['reason'] = reason
        return response
    if type(timeout) is not int or not 1 <= timeout <= 300:
        return gap('invalid_timeout')
    try:
        root = Path(directory)
        response['text_report'] = scan(root, read_policy(policy))
        if not response['text_report']['coverage_complete']:
            return gap('incomplete_text_scope')
        root = root.resolve()
        executable = Path(binary)
        if not executable.is_absolute() or executable.is_symlink() or not executable.is_file():
            return gap('engine_missing')
        if not re.fullmatch(r'[0-9a-f]{64}', digest or ''):
            return gap('invalid_engine_digest')
        with executable.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != digest:
            return gap('engine_digest_mismatch')
        env = {k: v for k, v in os.environ.items() if not k.startswith('GITLEAKS_')}
        with tempfile.TemporaryDirectory(prefix='guard-secrets-') as temp:
            work = Path(temp)
            # No engine logs or exception messages enter the response.
            version_file = work / 'version.txt'
            with version_file.open('wb') as output:
                result = subprocess.run([str(executable), 'version'], cwd=work, env=env,
                                        stdout=output, stderr=subprocess.DEVNULL, timeout=timeout)
            with version_file.open('rb') as stream:
                version = stream.read(257).decode('ascii', errors='replace').strip()
            if result.returncode != 0 or version != ENGINE_VERSION:
                return gap('engine_version_mismatch')
            snapshot = work / 'material'; snapshot.mkdir(); snapshot = snapshot.resolve()
            count, total = snapshot_text(root, snapshot, response['text_report']['limits'])
            if (count != response['text_report']['files_inspected'] or
                    total != response['text_report']['bytes_read']):
                return gap('scope_changed')
            config = work / 'config.toml'
            config.write_text('[extend]\nuseDefault = true\n', encoding='utf-8')
            ignore = work / '.gitleaksignore'; ignore.write_text('', encoding='utf-8')
            report = work / 'engine.json'
            args = [str(executable), 'dir', str(snapshot), '--config', str(config),
                    '--gitleaks-ignore-path', str(ignore), '--ignore-gitleaks-allow',
                    '--redact=100', '--no-banner', '--no-color', '--log-level', 'error',
                    '--exit-code', '10', '--report-format', 'json', '--report-path', str(report),
                    '--max-decode-depth', '0']
            result = subprocess.run(args, cwd=work, env=env, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=timeout)
            if result.returncode not in (0, 10):
                return gap('engine_failed')
            records = load_response(report, MAX_REPORT_BYTES)
            converted = convert(records, snapshot)
            if bool(converted) != (result.returncode == 10):
                return gap('engine_result_mismatch')
            response['findings'] = converted
            response['engine'].update(status='completed', reason=None)
    except subprocess.TimeoutExpired:
        return gap('engine_timeout')
    except (OSError, ValueError, RecursionError):
        return gap('input_or_engine_report_invalid')
    return response


def exit_code(response):
    text = response['text_report']
    if response['findings'] or (text and text['findings']):
        return 1
    return 0 if response['engine']['status'] == 'completed' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    parser.add_argument('--gitleaks', required=True)
    parser.add_argument('--engine-sha256', required=True)
    parser.add_argument('--policy')
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()
    response = inspect(args.directory, args.gitleaks, args.engine_sha256, args.policy, args.timeout)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return exit_code(response)


if __name__ == '__main__':
    sys.exit(main())

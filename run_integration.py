"""GitHub Action runner: retain JSON outside scope and preserve scanner status."""
import json
import os
from pathlib import Path
import sys
from publication_opsec_guard.guard import read_policy, scan


def run():
    directory = os.environ.get('GUARD_DIRECTORY', '.')
    policy = os.environ.get('GUARD_POLICY') or None
    report_path = Path(os.environ.get('GUARD_REPORT', ''))
    try:
        root = Path(directory).resolve()
        target = report_path.resolve()
        if not os.environ.get('GUARD_REPORT') or target == root or root in target.parents:
            raise ValueError('Report must be outside inspected scope')
        if report_path.is_symlink() or report_path.exists():
            raise ValueError('Report must be new')
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            report = scan(directory, read_policy(policy))
        except (OSError, ValueError, RecursionError):
            report = {'error': 'Invalid input or policy', 'status': 'not_tested'}
        code = 2 if 'error' in report else (1 if report['findings'] else 2 if not report['coverage_complete'] else 0)
        # Exclusive create prevents overwriting a report or following a target symlink.
        with target.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    except (OSError, ValueError, RecursionError):
        code = 2
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        try:
            with open(output, 'a', encoding='utf-8') as stream:
                stream.write(f'exit-code={code}\n')
        except OSError:
            code = 2
    print(f'Publication OPSEC Guard exit code: {code}')
    return code


if __name__ == '__main__':
    sys.exit(run())

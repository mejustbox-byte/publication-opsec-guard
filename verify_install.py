"""Build twice, install outside checkout, and verify installed console commands."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parent

def run(args, cwd, expected=0, env=None):
    result = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True,
                            text=True, encoding='utf-8', timeout=120, env=env)
    if result.returncode != expected:
        raise RuntimeError(f'Command failed ({result.returncode}): {result.stdout} {result.stderr}')
    return result

def main():
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        env = dict(os.environ, SOURCE_DATE_EPOCH='1700000000')
        env.pop('PYTHONPATH', None)
        wheels = []
        for name in ('first', 'second'):
            folder = temp / name
            run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
                 '--wheel-dir', folder, ROOT], temp, env=env)
            wheels.append(next(folder.glob('*.whl')))
        hashes = [hashlib.sha256(w.read_bytes()).hexdigest() for w in wheels]
        assert hashes[0] == hashes[1], 'Wheel bytes differ at fixed SOURCE_DATE_EPOCH'
        target = temp / 'installed'
        venv.EnvBuilder(with_pip=True).create(target)
        bindir = target / ('Scripts' if os.name == 'nt' else 'bin')
        python = bindir / ('python.exe' if os.name == 'nt' else 'python')
        suffix = '.exe' if os.name == 'nt' else ''
        scanner = bindir / ('publication-opsec-guard' + suffix)
        validator = bindir / ('publication-opsec-validate' + suffix)
        run([python, '-m', 'pip', 'install', '--no-index', '--no-deps', wheels[0]], temp, env=env)
        run([python, '-m', 'pip', 'check'], temp, env=env)
        material = temp / 'material'; material.mkdir()
        file = material / 'sample.txt'; file.write_text('safe', encoding='utf-8')
        clean = run([scanner, material], temp, env=env)
        assert json.loads(clean.stdout)['tool_version'] == '0.2.0a3'
        report = temp / 'report.json'; report.write_text(clean.stdout, encoding='utf-8')
        absent = run([validator, report], temp, expected=3, env=env)
        assert json.loads(absent.stdout)['errors'][0]['code'] == 'dependency_missing'
        file.write_text('10.1.2.3', encoding='utf-8')
        run([scanner, material], temp, expected=1, env=env)
        file.unlink(); run([scanner, material], temp, expected=2, env=env)
        run([python, '-m', 'pip', 'install', '-r', ROOT / 'requirements-validation.txt'], temp, env=env)
        run([python, '-m', 'pip', 'check'], temp, env=env)
        run([validator, report], temp, env=env)
        print('OK: deterministic wheel bytes at fixed epoch; clean installed scanner 0/1/2; validator missing dependency 3 and valid report 0')

if __name__ == '__main__':
    main()

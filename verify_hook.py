"""Exercise the real local pre-commit Python hook without remote hook checkout."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parent

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Use a copied checkout: no writes to the source repository.
        for name in ('publication_opsec_guard', 'schemas'):
            shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('pyproject.toml', 'README.md'):
            shutil.copy(ROOT / name, root / name)
        def command(args):
            return subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=120)
        assert command(['git', 'init']).returncode == 0
        material = root / 'materials'; material.mkdir()
        sample = material / 'sample.txt'; sample.write_text('safe')
        hook = yaml.safe_load((ROOT / '.pre-commit-hooks.yaml').read_text())[0]
        hook['args'] = ['materials']
        hook['additional_dependencies'] = [str(ROOT)]
        (root / '.pre-commit-config.yaml').write_text(yaml.safe_dump(
            {'repos': [{'repo': 'local', 'hooks': [hook]}]}))
        command(['git', 'add', '.'])
        for payload, expected in [('safe', 0), ('10.1.2.3', 1)]:
            sample.write_text(payload)
            result = command([sys.executable, '-m', 'pre_commit', 'run', '--all-files'])
            assert result.returncode == expected, result.stdout + result.stderr
        sample.unlink()
        (material / 'attachment.bin').write_bytes(b'unknown')
        result = command([sys.executable, '-m', 'pre_commit', 'run', '--all-files'])
        assert result.returncode == 1, result.stdout + result.stderr
        print('OK: real pre-commit environment accepts clean material and blocks findings and incomplete coverage')

if __name__ == '__main__':
    main()

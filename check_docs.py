"""Check paired Markdown, local links and executable synthetic examples."""
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from validate_report import validate_response

ROOT = Path(__file__).parent


def execute_block(block, directory, expected):
    last = None
    for line in block.strip().splitlines():
        tokens = shlex.split(line)
        assert tokens[0] == 'python3', 'Unsupported guide command'
        tokens[0] = sys.executable
        output = None
        if '>' in tokens:
            index = tokens.index('>')
            assert index == len(tokens) - 2, 'Unexpected redirection'
            output = Path(directory, tokens[-1])
            tokens = tokens[:index]
        last = subprocess.run(tokens, cwd=directory, capture_output=True, text=True,
                              encoding='utf-8', timeout=30)
        if output:
            output.write_text(last.stdout, encoding='utf-8')
        if output is None:
            assert last.returncode == 0, 'Guide setup failed'
    assert last is not None and last.returncode == expected, 'Guide exit mismatch'


def main():
    ru = {f.name for f in (ROOT / 'docs/ru').glob('*.md')}
    en = {f.name for f in (ROOT / 'docs/en').glob('*.md')}
    assert ru == en, 'Page pair mismatch'
    for file in [*ROOT.glob('README*.md'), *ROOT.glob('docs/*/*.md')]:
        text = file.read_text(encoding='utf-8')
        assert text.count('```') % 2 == 0, f'Unclosed fence: {file.name}'
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if not target.startswith(('https://', 'http://', '#')):
                assert (file.parent / target.split('#')[0]).is_file(), f'Broken link: {file.name}'
    for name in ru:
        pattern = r'```(?:bash|json|text|mermaid)?\n(.*?)```'
        a = (ROOT / 'docs/ru' / name).read_text(encoding='utf-8')
        b = (ROOT / 'docs/en' / name).read_text(encoding='utf-8')
        assert name == 'architecture.md' or re.findall(pattern, a, re.S) == re.findall(pattern, b, re.S), name
    guide = (ROOT / 'docs/en/user-guide.md').read_text(encoding='utf-8')
    blocks = re.findall(r'```bash\n(.*?)```', guide, re.S)
    with tempfile.TemporaryDirectory() as directory:
        shutil.copy(ROOT / 'guard.py', Path(directory, 'guard.py'))
        for block, code in zip(blocks[1:3], (1, 0)):
            execute_block(block, directory, code)
        before = json.loads(Path(directory, 'demo-report.json').read_text(encoding='utf-8'))
        after = json.loads(Path(directory, 'demo-report-after.json').read_text(encoding='utf-8'))
        assert [(f['check_id'], f['evidence']['line']) for f in before['findings']] == [
            ('PUB-001', 1), ('PUB-002', 2), ('PUB-005', 3)]
        assert after['files_inspected'] == 1 and after['coverage_complete'] and not after['findings']
        assert validate_response(before)['scanner_exit_code'] == 1
        assert validate_response(after)['scanner_exit_code'] == 0
    for lang in ('en', 'ru'):
        contract = (ROOT / 'docs' / lang / 'report-format.md').read_text(encoding='utf-8')
        example = json.loads(re.findall(r'```json\n(.*?)```', contract, re.S)[0])
        assert validate_response(example)['valid'], 'Documented report fails validation'
    for name, code in (('clean', 0), ('findings', 1), ('empty', 2), ('startup-error', 2)):
        result = subprocess.run([sys.executable, str(ROOT / 'validate_report.py'),
                                 str(ROOT / 'examples/reports/valid' / (name + '.json'))],
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == code, 'Validator example mismatch'
    result = subprocess.run([sys.executable, str(ROOT / 'validate_report.py'),
                             str(ROOT / 'examples/reports/invalid/false-clean.json')],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 3, 'Invalid example accepted'
    print(f'OK: {len(ru)} RU/EN page pairs, local links, code parity, guide 1->0, report schema and validator examples')


if __name__ == '__main__':
    main()

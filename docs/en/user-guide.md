# User guide: first inspection and workflow

## 1. Preparation

Use Git to obtain the repository and Python to run the script. No third-party Python dependencies are required. CI uses Python 3.13; other versions are not separately claimed compatible.

```bash
git clone https://github.com/mejustbox-byte/publication-opsec-guard.git
cd publication-opsec-guard
python3 --version
python3 guard.py --help
```

On Windows use `python` or `py -3` if that is your interpreter command. Examples below use `python3`; change the command name while preserving arguments.

## 2. Safe synthetic example

Create an input directory and a separate policy file. Keep the policy outside the input directory so its own markers do not become findings.

```bash
python3 -c "import json; from pathlib import Path; Path('demo-input').mkdir(exist_ok=True); Path('demo-input/notes.md').write_text('Management endpoint: 10.20.30.40\nEnvironment: demo.internal\nProject: SyntheticOrg\n', encoding='utf-8'); Path('demo-policy.json').write_text(json.dumps({'markers':['SyntheticOrg']}), encoding='utf-8')"
python3 guard.py demo-input --policy demo-policy.json > demo-report.json
```

Expected exit code: **1**. Three findings: PUB-001 on line 1, PUB-002 on line 2, PUB-005 on line 3. `demo-report.json` is outside `demo-input` and therefore is not part of the inspected material.

In a POSIX shell use `echo $?` for the preceding exit code; in PowerShell use `$LASTEXITCODE`. The scanner emits JSON; shell redirection creates the report file.

## 3. Interpret the result

Read `scope`, `files_inspected` and `coverage_gaps` first. For each finding, locate `asset_id` and `evidence.line` in the input copy. Raw matches are intentionally hidden; inspect context in a local editor.

A rule classifies an indicator. For example, a private IPv4 address may be an acceptable educational example. It still produces a finding: this version has no exceptions mechanism or reviewer-decision store.

## 4. Correct and inspect again

```bash
python3 -c "from pathlib import Path; Path('demo-input/notes.md').write_text('Management endpoint: 192.0.2.10\nEnvironment: example.invalid\nProject: Example project\n', encoding='utf-8')"
python3 guard.py demo-input --policy demo-policy.json > demo-report-after.json
```

Expected exit code: **0**, empty `findings` and `coverage_gaps`, `files_inspected: 1`. This means no supported-rule indicators were found in this text. It does not establish safety of other document formats or all secret types.

## 5. Inspect working material

1. Prepare a separate copy containing only material intended for sharing.
2. Store organization markers in a private local policy file.
3. Write the report outside the input directory.
4. Review every finding and every coverage gap.
5. Edit the copy and repeat with identical parameters.
6. Independently inspect unsupported material and identifying report filenames before publication.

Partially masking a private key does not make an exposed real key safe. If a real key has already been disclosed, replacement and revocation belong in its managing system. Guard does not perform those actions.

## 6. What success does not establish

Exit code 0 does not establish token absence, EXIF cleaning, Git-history inspection or screenshot OCR. An empty directory returns 2 and records `empty_scope`; exclusions also prevent complete coverage. See the [report contract](report-format.md) for field meanings.

---

[Documentation index](index.md) · [Русский](../ru/user-guide.md)

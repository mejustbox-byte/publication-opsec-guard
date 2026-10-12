# Publication OPSEC Guard

**Local publication preflight · Read-only · Explicit coverage · MIT**

Inspect prepared material for internal addresses, naming, user paths, private-key headers, configured markers and selected Office identity metadata. Reports hide matched values and retain untested coverage. **0.3.0a1 is an alpha**, with a bounded declared scope.

[Русский](README.ru.md) · [Full handbook](docs/en/index.md) · [Unified runner](docs/en/unified-inspection.md) · [Release notes](docs/en/release-notes.md)

## Supported inspection

| Component | Delivered |
|---|---|
| UTF-8 text | Five disclosure rules, strict local naming policy, bounded file traversal |
| DOCX/PPTX/XLSX | Bounded XML text and selected identity metadata; joined rich-text runs |
| Optional Gitleaks | Pinned user-installed 8.24.2 binary/digest; text-only specialist inspection |
| Unified runner | Mixed prepared directory, one aggregate report and explicit child states |
| Report validator | Core, document, secret and aggregate schemas plus cross-field checks |
| Integration | Text-only GitHub Action/pre-commit; mixed inspection through the unified CLI |

## Install and run

Use Python 3.12+ with current security patches; CI checks Python 3.13. From a reviewed checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[validation]'
.venv/bin/publication-opsec-inspect prepared-materials > publication-report.json
.venv/bin/publication-opsec-validate publication-report.json
```

On Windows use `.venv\Scripts\python.exe` and `.venv\Scripts\publication-opsec-inspect.exe`. Keep reports and private policies outside the inspected directory. Install `.` without the extra for scanning alone. Release wheel/source artifacts and SHA256SUMS are supplied through GitHub Releases; PyPI publication is not provided.

| Code | Meaning |
|---|---|
| 0 | No findings or recorded gaps in the declared scope |
| 1 | Findings exist; incomplete coverage may also exist |
| 2 | Incomplete coverage or input failure without findings |
| 3 | Validator-only: invalid report or unavailable validation |

## Alpha boundaries

PDF/OCR, general archives, embedded binaries/media and Office rendering are not inspected. Formulas are read as text, never calculated. Optional specialist secret inspection does not cover Office XML; requesting it leaves explicit document gaps. Actual Gitleaks execution is verified on Linux only. Zero is not a guarantee of no secrets or authorization to publish. Report paths remain identifying metadata.

## Evidence and documentation

The suite includes 84 unittest methods, synthetic rule/package corpora, clean installation checks and executable RU/EN guide checks. Dependency audit evidence is point-in-time; pins are not signatures or a fully hash-locked supply chain. See [check matrix](docs/en/check-matrix.md), [XLSX](docs/en/xlsx-inspection.md), [all-envelope validation](docs/en/all-report-validation.md), [threat model](docs/en/threat-model.md) and [limitations](docs/en/development-plan.md).

Licensed under [MIT](LICENSE). The project does not upload documents or automatically repair them.

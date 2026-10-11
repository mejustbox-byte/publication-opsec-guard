# User guide

Text prototype 0.1.0a1. Run from the project directory:

```bash
python3 guard.py /path/to/materials --policy policy.json
python3 -m unittest discover -v
```

Optional policy: `{"markers":["SyntheticOrg"]}`. Exit codes: 0 — supported text checked without findings; 1 — findings; 2 — incomplete coverage or error. Findings plus coverage gaps return 1; gaps remain in JSON. File limit 2 MB, file count limit 10000. .git and __pycache__ directories are intentionally excluded; Git history is not inspected. Results do not establish safety of all material. Save stdout outside the inspected directory. Report paths may identify files; sanitize before publication. Windows and macOS are not tested. Contents are never executed; symlinks are skipped. Text is decoded as UTF-8. No OCR, PDF/Office/archive support, IPv6 or comprehensive token scanning.

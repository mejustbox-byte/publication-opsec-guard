# Unified publication inspection

## One command, explicit scope

Version 0.3.0a1 adds `publication-opsec-inspect DIRECTORY`. It dispatches UTF-8 text and supported DOCX/PPTX/XLSX into one aggregate JSON response. It reads a prepared copy without modifying it. Install the package and optional validation dependencies as described in [installation](installation.md). Store reports outside the inspected directory and private policy files outside material intended for publication.

```bash
publication-opsec-inspect prepared-materials --policy policy.local.json > publication-report.json
publication-opsec-validate publication-report.json
```

The first command returns 0 when the declared scope has no findings or recorded gaps, 1 for findings (possibly with gaps), and 2 for incomplete/invalid inspection without findings. The validator preserves those meanings and returns 3 for invalid/unavailable validation. Shells commonly stop after a nonzero command; retain reports through an explicit failure-artifact step, never hide failure merely to publish.

## Dispatch and limits

The runner copies accepted regular files into a temporary text/Office staging tree. Text goes through the existing five-rule scanner; Office files go through the bounded document profile. Relative paths are preserved. Unknown extensions, PDF, images, archives, links and special files remain gaps; excluded Git/cache directories also prevent complete coverage. Empty input never succeeds.

Aggregate limits: 1,000 files, 1,000 directories, 50,000,000 read bytes, 100 Office documents and 10,000 top-level findings. Per-file copy limits are 2,000,000 text bytes or 8,000,000 Office bytes. Document XML limits remain separate. Budgets are not a hard total memory/CPU quota. Counts and copies do not authenticate an immutable source; use a stable prepared tree. Normal temporary-file deletion is not secure erasure.

## Optional Gitleaks

Secret inspection is explicit, not implicitly claimed for the default scope:

```bash
publication-opsec-inspect prepared-materials --gitleaks /absolute/path/gitleaks --engine-sha256 VERIFIED_BINARY_SHA256 > publication-report.json
```

The digest placeholder must be replaced with a verified binary hash. Version 8.24.2 and existing adapter safeguards apply. `secrets_requested: false` means the specialist engine was not requested, not that all secrets were tested. When requested it inspects staged text only. Each Office document receives `document_secret_engine_not_tested`, so the bundle remains incomplete even if Office generic checks passed. Missing/failed engine and incomplete configuration remain visible. The core Action/hook stays text-only; run this CLI in a separate pipeline step for mixed publications.

## Aggregate contract

`bundle-0.1` contains scope/version, secrets_requested, coverage_complete, counters/limits, nullable text_report, document reports, nullable secrets_report and runner coverage_gaps. Child responses retain their own schema versions. Text report is null when no text was present; a document-only bundle can still complete its declared XML scope. Coverage is complete only if runner and every requested child inspection complete. Exit 1 does not imply complete coverage. Paths remain sensitive metadata even though matching values are hidden.

[Bundle schema](../../schemas/bundle-0.1.schema.json) and [all-format validation](all-report-validation.md) document consumer requirements. No PDF/OCR, general archive inspection, online token validation, automatic cleaning or publication authorization is supplied.

---

[Documentation index](index.md) · [Русский](../ru/unified-inspection.md)

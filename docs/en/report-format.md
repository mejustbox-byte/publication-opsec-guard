# JSON report contract 0.2

## Purpose

Reports support local review and publication-pipeline integration. The format is a JSON object with a bundled [Draft 2020-12 schema](../../schemas/response-0.2.schema.json) and [standalone validator](report-validation.md). Do not assume fields from the future shared OPSEC contract already exist here.

## Finding example

```json
{
  "schema_version": "0.2",
  "tool_version": "0.2.0a2",
  "scope": "utf8-text-only",
  "coverage_complete": true,
  "files_inspected": 1,
  "files_encountered": 1,
  "bytes_read": 9,
  "scan_stopped": false,
  "limits": {
    "max_bytes": 2000000,
    "max_files": 10000,
    "max_total_bytes": 50000000,
    "max_findings": 10000,
    "max_directories": 10000
  },
  "exclusions": [],
  "findings": [
    {
      "check_id": "PUB-001",
      "asset_id": "notes.md",
      "status": "fail",
      "severity": "high",
      "evidence": {
        "line": 1,
        "redacted": true
      },
      "remediation": "Replace internal addresses with documentation addresses."
    }
  ],
  "coverage_gaps": []
}
```

`coverage_complete: true` can coexist with findings: it describes recorded processing gaps, while findings describe content. It is not a safety score.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Result shape version; currently `0.2` |
| `tool_version` | string | Implementation version; currently `0.2.0a2` |
| `scope` | string | `utf8-text-only`; bounds interpretation |
| `coverage_complete` | boolean | True exactly when both gaps and exclusions are empty |
| `files_inspected` | integer | Successfully read and decoded supported files |
| `files_encountered` | integer | Files encountered before stopping, including unsupported files |
| `bytes_read` | integer | Input bytes actually read, excluding policy bytes |
| `scan_stopped` | boolean | Resource limit stopped traversal; ordinary skips alone leave false |
| `limits` | object | Five effective limits, named as CLI flags with underscores |
| `exclusions` | array | Intentionally skipped directories |
| `findings` | array | Individual matches, not every executed check |
| `coverage_gaps` | array | Skips, processing errors and file-count limit |

Intentional `.git` and `__pycache__` exclusions are listed in `exclusions`, with `asset_id` and `reason: excluded_directory`; they make coverage incomplete. If zero files are inspected, `empty_scope` is recorded, even when other gaps already exist. Reports contain no timestamp, hostname, input-file hashes or policy hash; alone they do not establish which exact bytes were inspected.

## Finding record

`check_id` identifies a rule; `asset_id` is a relative path, not a global stable asset identity. `status` is always `fail`. `severity` is the rule's static value. `evidence.line` is an integer; lines are counted by `\n` starting at 1. `redacted` is always `true`; column and raw match are omitted. `remediation` is static English text regardless of documentation language.

There are no individual `pass` or `not_applicable` records, asset aggregation or finding IDs. Consumers must not infer a passed check from an absent record without evaluating coverage.

## Coverage gaps

```json
{
  "asset_id": "diagram.png",
  "status": "not_tested",
  "reason": "unsupported_format"
}
```

| `reason` | Meaning | Response |
|---|---|---|
| `unsupported_format` | Filename/extension outside the supported set | Inspect another way; do not rename binary files to bypass checks |
| `symlink` | Symbolic link skipped | Prepare a normal isolated copy of the needed file |
| `size_limit` | File exceeds `max_bytes` | Review resource risk; split material or justify a larger limit |
| `binary_content` | NUL byte present | Inspect its format using another tool |
| `not_regular_file` | Object is not a regular file | Remove special objects from the prepared copy |
| `unreadable_or_invalid_utf8` | Read or UTF-8 error | Check permissions and encoding; do not automatically rewrite originals |
| `directory_unreadable` | Directory traversal error | Review access; the record has no path |
| `file_count_limit` | Encountered a file beyond the limit | Narrow scope or justify a limit change; traversal stopped |
| `total_bytes_limit` | Aggregate read budget exhausted | Narrow the prepared copy; inspect the remainder separately |
| `finding_count_limit` | A further match would exceed retained findings | Resolve existing findings and rerun; output is partial |
| `directory_count_limit` | Directory traversal/fanout budget exceeded | Narrow the directory tree |
| `empty_scope` | No supported file successfully inspected | Correct scope or inspect formats another way |

`directory_unreadable`, `file_count_limit`, `directory_count_limit` and `empty_scope` omit `asset_id`. Integrations must handle its absence instead of assuming the key is mandatory.

## Startup error

```json
{"error": "Invalid input or policy", "status": "not_tested"}
```

This is a different object without normal report fields. Check `error` first, then `schema_version` and `scope`. Do not store it as a successful audit. Separately handle argparse errors, which emit no JSON.

## Privacy and retention

Match redaction reduces value disclosure, but paths remain readable. Before external sharing, replace identifying filenames or share aggregate counts only. Retention, access and deletion are organization workflow decisions; the scanner does not manage them.

## Migration from 0.1

Require `schema_version: 0.2` for the new fields. Do not fill missing 0.1 exclusions or counters with invented values. Empty input previously returned 0; now it returns 2. Excluded directories previously left coverage unchanged; now they make it incomplete. Findings still take code-1 priority. These deliberate changes prevent an empty or partially excluded tree being treated as a clean review. A schema file and standalone validator are now delivered; cross-field consistency requires the validator in addition to structural schema checks.

---

[Documentation index](index.md) · [Русский](../ru/report-format.md)

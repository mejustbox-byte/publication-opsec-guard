# JSON report contract 0.1

## Purpose

Reports support local review and publication-pipeline integration. The current format is a plain JSON object; a separate JSON Schema validator is not shipped. Do not assume fields from the future shared OPSEC contract already exist here.

## Finding example

```json
{
  "schema_version": "0.1",
  "tool_version": "0.1.0a1",
  "scope": "utf8-text-only",
  "coverage_complete": true,
  "files_inspected": 1,
  "findings": [
    {
      "check_id": "PUB-001",
      "asset_id": "notes.md",
      "status": "fail",
      "severity": "high",
      "evidence": {"line": 1, "redacted": true},
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
| `schema_version` | string | Result shape version; currently `0.1` |
| `tool_version` | string | Implementation version; currently `0.1.0a1` |
| `scope` | string | `utf8-text-only`; bounds interpretation |
| `coverage_complete` | boolean | True exactly when no `coverage_gaps` are recorded |
| `files_inspected` | integer | Successfully read and decoded supported files |
| `findings` | array | Individual matches, not every executed check |
| `coverage_gaps` | array | Skips, processing errors and file-count limit |

Intentional `.git` and `__pycache__` exclusions do not create gaps. An empty directory can have `coverage_complete: true`, `files_inspected: 0`. Reports contain no timestamp, hostname, input-file hashes or policy hash; alone they do not establish which exact bytes were inspected.

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

The last two reasons omit `asset_id`. Integrations must handle its absence instead of assuming the key is mandatory.

## Startup error

```json
{"error": "Invalid input or policy", "status": "not_tested"}
```

This is a different object without normal report fields. Check `error` first, then `schema_version` and `scope`. Do not store it as a successful audit. Separately handle argparse errors, which emit no JSON.

## Privacy and retention

Match redaction reduces value disclosure, but paths remain readable. Before external sharing, replace identifying filenames or share aggregate counts only. Retention, access and deletion are organization workflow decisions; the scanner does not manage them.

---

[Documentation index](index.md) · [Русский](../ru/report-format.md)

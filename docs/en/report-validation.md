# Report validation: schema, consistency and integration

## What the validator is for

A downstream consumer must distinguish a clean supported-text review, findings, incomplete coverage, a startup error and a malformed response. Merely parsing JSON cannot establish that distinction. `validate_report.py` checks the bundled contract 0.2 and then verifies cross-field invariants before deriving the scanner's exit code.

Validation reads an existing report. It does not rescan source files, reopen `asset_id` paths or contact a service. It does not establish that the report was produced by Guard or that its counters describe the actual source copy. A fabricated but internally consistent report can pass: signatures, source hashes and provenance are not supplied.

## Installation and environment

The scanner `guard.py` still requires only the standard library. The optional validator uses `jsonschema==4.26.0` and version-pinned transitive dependencies in [requirements-validation.txt](../../requirements-validation.txt). Use Python 3.13 for the CI-tested configuration. Local development also ran on Python 3.12; this is not a matrix of every minor release or architecture.

Create an isolated environment:

```bash
python3 -m venv .venv
```
Activate it with `source .venv/bin/activate` on POSIX, or `.venv\Scripts\Activate.ps1` in PowerShell. Then install and run a supplied clean response:

```bash
python3 -m pip install -r requirements-validation.txt
python3 -m pip check
python3 validate_report.py examples/reports/valid/clean.json
```
The final command returns 0 and emits validation JSON. Installation downloads dependencies unless a prepared wheel cache is used. Validation itself does not fetch remote schemas; the retrieval registry denies external references. Exact package versions do not constitute a hash-locked environment, vulnerability audit or reproducible binary build. Preserve the entire `schemas` directory next to the script.

## CLI

```text
python3 validate_report.py REPORT
  [--max-report-bytes N] [--max-errors N]
```
| Argument | Default | Meaning |
|---|---|---|
| `REPORT` | Required | Regular UTF-8 JSON file; symlinks are rejected |
| `--max-report-bytes` | `16000000` | Input read bound, separate from the scanner's content budget |
| `--max-errors` | `32` | Maximum retained diagnostic records |

Limits must be positive integers. The JSON nesting limit is fixed at 64. Duplicate keys at any depth, malformed UTF-8/JSON, BOM, NaN/Infinity, excessive depth and special files fail closed. An input read probes one byte beyond the configured maximum to detect oversize input. Do not increase limits without evaluating available process resources.

## Exit codes and output

```json
{
  "valid": true,
  "kind": "report",
  "scanner_exit_code": 0,
  "errors": [],
  "errors_truncated": false
}
```
| Exit | Meaning | Consumer response |
|---|---|---|
| `0` | Valid report, complete declared coverage, no findings | Continue local review of scope and provenance |
| `1` | Valid report with findings; gaps may coexist | Handle findings and inspect coverage |
| `2` | Valid incomplete report without findings, or recognized startup error | Resolve the missing inspection or input/policy error |
| `3` | Invalid/unreadable report or unavailable validation | Stop integration; never substitute a clean result |

`valid` describes conformity, not publication approval. `kind` is `report`, `startup_error` or `invalid`. `scanner_exit_code` is null for invalid input. `errors` records a stable `code` and safe `location`; `errors_truncated` indicates additional errors beyond the cap. Locations identify contract fields and array indices, not source paths. Diagnostics omit instance values, unexpected property names and exception messages. Argument-syntax errors are argparse diagnostics on stderr with code 2 and no validation JSON; closed output pipes are not normalized.

Try the supplied examples:

```bash
python3 validate_report.py examples/reports/valid/findings.json
python3 validate_report.py examples/reports/valid/empty.json
python3 validate_report.py examples/reports/valid/startup-error.json
python3 validate_report.py examples/reports/invalid/false-clean.json
```
Expected exit codes, in order: 1, 2, 2, 3. A recognized startup error is well-formed but unsuccessful; it must never advance a publication gate. In POSIX use `echo $?`, in PowerShell `$LASTEXITCODE` immediately after each command.

## Structural checks

[response-0.2.schema.json](../../schemas/response-0.2.schema.json) declares Draft 2020-12. A response is either the complete report object or the exact startup-error envelope. Every object rejects additional fields. Required fields, types, contract/scope constants and numeric bounds are checked. Finding records enforce the rule ID's static severity and remediation; evidence must have a positive line and `redacted: true`, without raw evidence fields. Gap reasons determine whether `asset_id` is required or forbidden.

The schema uses local fragment references only. It can be consumed by another Draft 2020-12 implementation, but external structural validation alone does not enforce the consistency rules below. Standard reference: [JSON Schema validation vocabulary](https://json-schema.org/draft/2020-12/json-schema-validation); engine reference: [jsonschema validation API](https://python-jsonschema.readthedocs.io/en/stable/validate/).

## Cross-field checks

| Code | Invariant | Why it matters |
|---|---|---|
| `coverage_mismatch` | Complete iff gaps and exclusions are both empty | Prevent a partial report claiming full coverage |
| `empty_scope_mismatch` | Exactly one `empty_scope` iff zero files inspected | Empty review is not clean evidence |
| `stop_state_mismatch` | Stop flag iff a global-limit gap exists; at most one such gap | Preserve early-stop semantics |
| `file_counter_mismatch` | Inspected ≤ encountered | Reject impossible counters |
| `file_budget_exceeded` | Encountered ≤ `max_files` | Preserve the reported budget |
| `byte_budget_exceeded` | Bytes read ≤ `max_total_bytes` | Preserve aggregate-read accounting |
| `finding_budget_exceeded` | Retained findings ≤ `max_findings` | Reject inconsistent retention |
| `finding_limit_mismatch` | Finding-limit gap requires the cap to be filled | Overflow must follow the retained cap |
| `finding_without_input` | Findings require inspected files and bytes read | Reject a finding without inspected input |
| `file_limit_mismatch` | File-limit gap requires encountered count to equal its cap | Preserve scanner stopping behavior |

Schema integers follow JSON Schema numeric semantics: `1.0` is an integer value; `true` is a boolean, not an integer. The validator does not reconstruct line counts, prove per-file reads, verify match correctness or measure precision/recall.

## Safe consumer integration

First inspect the validator process code, then parse its JSON. Treat missing output, unsupported version, invalid JSON and code 3 as integration failures. Persist source scanning parameters and the original scanner process code in private pipeline metadata; compare that code with `scanner_exit_code` if both are available. The validator does not receive the original code and cannot make that comparison itself.

Do not open report asset paths on the consumer host. They are opaque source labels, may identify people and may use another OS's separator. Keep reports private. Do not publish validation inputs to debug a failure; reproduce with synthetic fixtures instead. A valid response does not grant permission to publish source material.

## Troubleshooting

| Diagnostic | Interpretation | Action |
|---|---|---|
| `input_error` | Missing/oversize/symlink/special file, bad encoding or strict JSON failure | Inspect local input safely; do not expect detailed value-bearing errors |
| `dependency_missing` | Optional validator dependency unavailable | Activate the environment and install requirements |
| `validation_unavailable` | Bundled schema missing/invalid or engine failure | Restore the script and schema from one verified checkout |
| `schema_*` | Structural constraint failed | Use safe field location, compare with contract; do not rename fields blindly |
| Consistency code | Counters/coverage/stop state disagree | Reproduce from scanner output; investigate producer or transport changes |
| `errors_truncated: true` | More than the retained number of diagnostics | Fix reported errors and rerun, or justify a larger cap |

## Reproducing quality checks

```bash
python3 -m unittest discover -v
python3 check_docs.py
```
The full suite contains 37 test methods: 22 scanner tests and 15 validator tests. Fifteen labeled report fixtures cover eight valid and seven invalid responses in [manifest.json](../../examples/reports/manifest.json). They measure contract scenarios, not disclosure-detection accuracy. `check_docs.py` verifies RU/EN page names, local links, command parity, the scanner guide's 1 → 0 sequence, documented report conformity and validator examples.

---

[Documentation index](index.md) · [Русский](../ru/report-validation.md)

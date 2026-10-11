# CLI and local policy reference

## Syntax

```text
python3 guard.py directory [--policy PATH] [--max-bytes N] [--max-files N]
  [--max-total-bytes N] [--max-findings N] [--max-directories N]
```

| Argument | Value | Default | Meaning |
|---|---|---|---|
| `directory` | Directory path | Required | Must exist and must not be a root symlink |
| `--policy` | JSON path | Unset | Loads organization markers; need not be inside the input directory |
| `--max-bytes` | Positive integer | `2000000` | Maximum bytes per file before decoding |
| `--max-files` | Positive integer | `10000` | Maximum encountered files, including unsupported ones |
| `--max-total-bytes` | Positive integer | `50000000` | Aggregate bytes actually read, including invalid files and size probes |
| `--max-findings` | Positive integer | `10000` | Maximum retained findings; a further valid match stops traversal |
| `--max-directories` | Positive integer | `10000` | Traversal/fanout budget, including the root |
| `-h`, `--help` | No value | — | Emits argparse help, not a JSON report |

Quote paths containing spaces using your shell's syntax. There is no `--output`, `--exclude`, `--format`, `--language`, allowlist or repair mode. Exceeding `max_files` stops the entire walk; individual file errors allow inspection to continue.

## Policy

```json
{
  "markers": ["SyntheticOrg", "Project Falcon"]
}
```

The root must be an object and `markers` a list of nonempty strings. Empty objects and lists are allowed. Whitespace-only strings are rejected. Whitespace around a nonempty marker is preserved: `" Team "` searches including those spaces. Matching ignores case and escapes regex metacharacters.

Markers match substrings, not word boundaries. A short marker such as `IT` can match within another word. Case-insensitive duplicate markers are rejected. Distinct overlapping patterns can still produce multiple findings. Unknown fields, including a misspelled `marker`, and duplicate JSON keys are rejected.

Policy is a regular nonsymlink UTF-8 file of at most 65,536 bytes. At most 128 markers are allowed, each up to 256 Unicode characters; NUL is forbidden. Empty `{}` and `{"markers": []}` disable PUB-005. Keep policy outside the input tree so it does not match its own markers. Invalid policy returns code 2; it never silently disables a requested check.

## Choosing resource limits

Keep defaults for a small prepared text copy. Lower budgets for untrusted inputs instead of raising them to force a clean result. `--max-total-bytes` counts bytes read, including rejected encoding and the one-byte oversize probe; it is not the sum of successfully inspected file sizes. Policy bytes use a separate 65,536-byte bound.

A file that does not fit the remaining aggregate budget is left uninspected, and traversal stops with `total_bytes_limit`. Exactly consuming the budget on the final file succeeds; attempting another supported file stops. Findings stop only when a further valid match would exceed their cap: exactly the allowed number can still yield complete coverage. The partially processed file is included in `files_inspected` because it was fully read and decoded; `scan_stopped` and the gap show that rule execution stopped early.

The directory budget includes the root and also checks immediate child count against the remaining budget before excluding directories. This deliberately conservative check may stop even when some children would have been excluded. It does not prevent `os.walk` from first allocating directory-entry lists. These budgets are not a process memory or execution-time sandbox.

## Exit codes

| Code | Condition | Integration response |
|---|---|---|
| `0` | No findings, gaps or exclusions; at least one file inspected | Review scope, file count and intentional exclusions |
| `1` | At least one finding | Review findings; coverage gaps may also be present |
| `2` | No findings but gaps/exclusions; or invalid input/policy | Resolve the reason or use another inspection method |

Invalid root or policy produces `{"error":"Invalid input or policy","status":"not_tested"}` on stdout. Argument syntax errors are handled by argparse: diagnostics/help on stderr, code 2, no JSON report. Output-write failures such as a closed pipe are not normalized by this contract.

---

[Documentation index](index.md) · [Русский](../ru/cli-reference.md)

# CLI and local policy reference

## Syntax

```text
python3 guard.py directory [--policy PATH] [--max-bytes N] [--max-files N]
```

| Argument | Value | Default | Meaning |
|---|---|---|---|
| `directory` | Directory path | Required | Must exist and must not be a root symlink |
| `--policy` | JSON path | Unset | Loads organization markers; need not be inside the input directory |
| `--max-bytes` | Positive integer | `2000000` | Maximum bytes per file before decoding |
| `--max-files` | Positive integer | `10000` | Maximum encountered files, including unsupported ones |
| `-h`, `--help` | No value | — | Emits argparse help, not a JSON report |

Quote paths containing spaces using your shell's syntax. There is no `--output`, `--exclude`, `--format`, `--language`, allowlist or repair mode. Exceeding `max_files` stops the entire walk; individual file errors allow inspection to continue.

## Policy

```json
{
  "markers": ["SyntheticOrg", "Project Falcon"]
}
```

The root must be an object and `markers` a list of nonempty strings. Empty objects and lists are allowed. Whitespace-only strings are rejected. Whitespace around a nonempty marker is preserved: `" Team "` searches including those spaces. Matching ignores case and escapes regex metacharacters.

Markers match substrings, not word boundaries. A short marker such as `IT` can match within another word. Duplicate markers and overlapping patterns can produce duplicate findings. Unknown policy fields are currently ignored: misspelling `markers` as `marker` does not cause an error and does not enable the organization check.

The policy uses `Path.read_text()` without an explicit `encoding`: for portable alpha policies use ASCII markers or verify the local encoding. Input files explicitly use UTF-8. Strict schema validation and explicit UTF-8 policy loading are planned.

## Exit codes

| Code | Condition | Integration response |
|---|---|---|
| `0` | No findings or recorded gaps | Review scope, file count and intentional exclusions |
| `1` | At least one finding | Review findings; coverage gaps may also be present |
| `2` | No findings but coverage gaps; or invalid input/policy | Resolve the reason or use another inspection method |

Invalid root or policy produces `{"error":"Invalid input or policy","status":"not_tested"}` on stdout. Argument syntax errors are handled by argparse: diagnostics/help on stderr, code 2, no JSON report. Output-write failures such as a closed pipe are not normalized by this contract.

---

[Documentation index](index.md) · [Русский](../ru/cli-reference.md)

# Optional Gitleaks adapter

## Purpose and installation

`publication-opsec-secrets` adds specialist secret-pattern inspection to the five text disclosure checks. Install the Guard package from a reviewed checkout. Separately obtain **Gitleaks 8.24.2** from its upstream release and verify the release archive checksum; compute SHA-256 of the extracted executable and retain it privately with the reviewed version. The adapter never downloads or updates the engine. Gitleaks upstream uses the MIT license; its own release files and rules remain upstream artifacts rather than vendored code.

This is a pinned compatibility baseline, not a claim that 8.24.2 is the newest or vulnerability-free release. Engine updates require a separate compatibility/security review. Consult [upstream usage and license](https://github.com/gitleaks/gitleaks) and [pinned release](https://github.com/gitleaks/gitleaks/releases/tag/v8.24.2).

## Invocation and decisions

Use an absolute executable path and the 64 lowercase hexadecimal digest of that exact binary. The placeholder below must be replaced; it is not a valid digest. Keep output outside the input directory:

```bash
publication-opsec-secrets prepared-materials --gitleaks /absolute/path/gitleaks --engine-sha256 VERIFIED_BINARY_SHA256 --timeout 30 > secrets-report.json
```

`--policy` optionally supplies the existing literal-marker policy. `--timeout` is an integer from 1 to 300 seconds, default 30; it applies separately to version probing and engine inspection. Codes: 1 if either text or secret findings exist; otherwise 2 if the engine is not completed; otherwise 0. Thus code 1 can coexist with an unavailable engine: always examine `engine.status` and the embedded text coverage. The existing core Action/hook still runs only the five-rule text scanner; invoke this additional command as a separate CI gate if secret inspection is required.

## Execution pipeline

1. Run the existing read-only text preflight and retain its contract-0.2 report.
2. If coverage is incomplete, do not launch the engine; report `incomplete_text_scope`.
3. Require an absolute regular executable, exact SHA-256 and version output `8.24.2`.
4. Copy the inspected UTF-8 file tree into a private temporary directory, rechecking regular files, symlinks, file count, per-file/total byte limits and counters.
5. Use an explicit temporary config extending the pinned engine defaults, an empty ignore file and `--ignore-gitleaks-allow`; strip inherited GITLEAKS_* variables. Archive files are rejected by the text preflight; decoding is disabled. Inspection uses directory mode, not Git history.
6. Discard engine stdout/stderr, request redaction and JSON, and use finding exit code 10 so ordinary engine errors are not confused with findings.
7. Load at most 4,000,000 report bytes with strict JSON checks and depth 64; accept at most 10,000 findings. Require exit-code/report agreement. Convert only rule ID, relative file and positive line number; discard Secret, Match, Line, Description, fingerprint, authors and other fields.
8. Remove temporary data on normal cleanup and return the independent envelope.

The preflight and snapshot are separate reads. Count/byte comparison detects some changes, not every concurrent modification. Use an immutable prepared copy. Unsupported formats, excluded directories, empty scope and unreadable files prevent engine execution. Engine default allowlists still apply; there is no claim of exhaustive secret discovery.

## Response contract: secrets-0.1

This new envelope is deliberately separate from the existing response-0.2 schema. `publication-opsec-validate` accepts core responses only and now supports this envelope. The CLI supplies `schema_version`, `tool_version`, `engine`, `text_report` and `findings`. `text_report` is a full original report or null on input failure. `engine` contains name, required version, status and reason; completed inspection has reason null. Secret findings contain `engine_rule`, `asset_id`, status fail and evidence with line/redacted=true. Filenames and rule IDs remain metadata, so keep reports access-controlled.

## Failure states

| Reason | Meaning and response |
|---|---|
| invalid_input / invalid_timeout | Fix command arguments or scope |
| incomplete_text_scope | Resolve text coverage gaps; engine was not started |
| engine_missing | Supply an absolute regular executable |
| invalid_engine_digest / engine_digest_mismatch | Review the binary and supply its verified digest |
| engine_version_mismatch | Install the pinned release; raw probe output is withheld |
| engine_timeout | Reduce scope or review bounded timeout; result is untested |
| engine_failed | Nonfinding engine error; output is suppressed |
| engine_result_mismatch | Engine status contradicts report contents |
| scope_changed | Snapshot counters differ from preflight |
| input_or_engine_report_invalid | Read, snapshot, encoding, report shape/size or metadata failure |

## Verification and practical limits

Eight adapter test methods cover clean/finding conversion, hidden sentinel values, unavailable engine, digest/version mismatch, timeout, engine error, malformed/contradictory reports, unexpected paths, incomplete scope, invalid policy, report size and snapshot counters. All platform runners run these fixtures. The real-engine CI check is Linux-only: it downloads the pinned release, verifies its published archive checksum and tests clean text, a nonfunctional token-shaped fixture and disabling inline allow comments. Windows/macOS actual-engine execution remains unverified.

The executable is trusted local code. Version/digest checks are not signature verification or process/network isolation. There is no hard process memory or temporary-disk quota; report size is enforced when reading after engine completion. Timeout kills the direct child; descendant containment is not established. Temporary copies contain sensitive text; normal deletion is not secure erasure. No online credential validation is requested. Fixture success does not prove real token validity, complete finding coverage or publication authorization.

---

[Documentation index](index.md) · [Русский](../ru/secret-adapter.md)

[All-report validation](all-report-validation.md) is supplied from 0.3.0a1.

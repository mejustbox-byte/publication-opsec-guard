# Requirements, implementation and evidence matrix

## Rules

| Requirement | Implementation | Supporting test | Test gap |
|---|---|---|---|
| PUB-001: RFC1918 | `RULES`, `private_v4()` | `test_all_rules_and_redaction`, `test_private_range_boundaries`, `test_documentation_ip_and_invalid_ip` | No comprehensive representation, Unicode or obfuscation corpus |
| PUB-002: .local/.internal | `RULES` regex | `test_all_rules_and_redaction` | No dedicated negative/boundary-name corpus |
| PUB-003: home paths | `RULES` regex | `test_all_rules_and_redaction` | Test uses Linux path; separate macOS/Windows representations are not covered |
| PUB-004: key headers | `RULES` regex | `test_all_rules_and_redaction` | Not every header variant has a dedicated test |
| PUB-005: markers | `re.escape`, `re.I` | `test_all_rules_and_redaction`, `test_marker_is_literal` | Duplicate and UTF-8 policy regressions exist; broader representation accuracy remains unmeasured |

## Processing and interface

| Requirement | Test | Establishes | Does not establish |
|---|---|---|---|
| Hidden values | `test_all_rules_and_redaction` | Four synthetic values absent from serialization | Full path/context anonymization |
| Clean text | `test_clean` | Empty findings without gaps | Absence of all possible secrets |
| Symlink/format | `test_symlink_and_unsupported` | Symlink/format gaps plus empty scope | Parent races, hardlinks or full permission matrix |
| Size/encoding/NUL | `test_size_encoding_and_binary` | Three files produce gaps | Every decoding/permission failure |
| File limit | `test_file_limit` | `file_count_limit` occurs | Aggregate resource ceiling |
| CLI | `test_exit_codes_and_invalid_policy` | Codes 0/1/2, empty marker, zero limit | Every malformed policy or stdout failure |

## CI evidence

[Run 38153720204](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38153720204): nine tests passed for `ubuntu-latest`, `windows-latest`, `macos-latest` at head `540e1124cd2ad35f08234df589a2f07af3357dce`. Code was then merged as `6347596d5ce6e13fe3692fdcb0bf58a9fb7ceea4`.

This establishes a specific test suite on hosted runners. It does not replace user-environment testing, corpus accuracy measurement or real-document operational validation. Every new support claim must add a test and result to this matrix.

## Hardening regressions in 0.2

| Area | Test methods | Evidence |
|---|---|---|
| Scope | `test_exact_env`, `test_empty_scope`, `test_exclusions_visible` | Exact `.env` inspected; empty and excluded scope cannot be clean |
| Bytes | `test_total_bytes_limit_and_exact_boundary`, `test_invalid_files_consume_byte_budget` | Aggregate limit, exact boundary, rejected-input accounting |
| Findings | `test_finding_limit_and_exact_boundary` | Cap retains allowed matches; overflow remains visible |
| Traversal | `test_directory_limit` | Root included; excessive child fanout stops |
| Policy | `test_policy_utf8`, `test_policy_unknown_and_duplicate_fields`, `test_policy_limits_and_duplicate_markers` | Cyrillic markers, unknown/duplicate keys, malformed roots, byte/marker caps |
| API | `test_positive_integer_api_limits` | Reject zero, negative, boolean and noninteger budget |
| Location | `test_newline_line_numbers` | Repeated markers report correct lines |
| CLI | `test_cli_empty_unknown_utf8_and_limits` | Empty scope, Cyrillic policy, typo and budget exit behavior |

The scanner subset contains 22 test methods. These tests verify behavior on synthetic inputs, not exhaustive rule accuracy, race resistance or bounded process memory.

## Previous hardening verification

All 22 tests passed on Linux, Windows and macOS with Python 3.13 in [run 38155720812](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38155720812) at implementation head `197f07d563b25193c86ab011e8bfd0798e005bc1`. Documentation links, language parity and the user-guide example were checked locally.

## Contract and consumer validation

| Requirement | Supporting tests | Evidence and limit |
|---|---|---|
| Standards-based schema | `test_schema_and_labeled_fixtures` | Schema meta-validation; 15 labeled responses; no claim of full detection corpus |
| Producer compatibility | `test_live_scanner_outputs` | Actual empty/.env/budget/encoding/tree responses accepted |
| Strict structure | `test_required_fields_and_unknown_envelopes`, `test_schema_types_and_unknown_fields`, `test_finding_shape_redaction_and_static_rule_mapping`, `test_gap_assets_and_unknown_reasons` | Missing/unknown fields, booleans, static rules, raw evidence and gap assets rejected |
| Internal consistency | `test_coverage_and_empty_scope_consistency`, `test_stop_state_consistency`, `test_budget_and_counter_consistency` | Coverage, counters and stop invariants; source authenticity remains unproven |
| Resource/input checks | `test_error_cap_and_numeric_integer_semantics`, `test_strict_json_and_read_boundaries`, `test_symlink_and_special_file_rejection` | Error/read/depth limits and strict JSON; no total-process sandbox |
| Safe execution | `test_no_network_during_validation`, `test_cli_result_codes_and_safe_errors`, `test_unavailable_schema_fails_closed` | No network attempt for bundled schema; codes 0–3; absent dependency/schema never succeeds |
| Bilingual examples | `check_docs.py` | Local links, 17 page pairs, command parity and executable scanner/validator examples |

The full suite contains 37 methods. See [validator guide](report-validation.md) for exact consumer semantics.

## Current verification: 0.2.0a2

All 37 test methods, `pip check` and `check_docs.py` passed on Linux, Windows and macOS with Python 3.13 in [run 38156874002](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38156874002) at implementation/documentation head `5fb0da0e6f67e2898b4cb1877cb68ae76a0e8f9b`. The run verifies dependency installation, 17 RU/EN page pairs and executable examples; it does not establish Intel Mac compatibility or source authenticity.

---

[Documentation index](index.md) · [Русский](../ru/check-matrix.md)

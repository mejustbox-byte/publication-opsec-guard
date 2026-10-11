# Requirements, implementation and evidence matrix

## Rules

| Requirement | Implementation | Supporting test | Test gap |
|---|---|---|---|
| PUB-001: RFC1918 | `RULES`, `private_v4()` | `test_all_rules_and_redaction`, `test_private_range_boundaries`, `test_documentation_ip_and_invalid_ip` | No comprehensive representation, Unicode or obfuscation corpus |
| PUB-002: .local/.internal | `RULES` regex | `test_all_rules_and_redaction` | No dedicated negative/boundary-name corpus |
| PUB-003: home paths | `RULES` regex | `test_all_rules_and_redaction` | Test uses Linux path; separate macOS/Windows representations are not covered |
| PUB-004: key headers | `RULES` regex | `test_all_rules_and_redaction` | Not every header variant has a dedicated test |
| PUB-005: markers | `re.escape`, `re.I` | `test_all_rules_and_redaction`, `test_marker_is_literal` | No separate duplicate/policy-encoding tests |

## Processing and interface

| Requirement | Test | Establishes | Does not establish |
|---|---|---|---|
| Hidden values | `test_all_rules_and_redaction` | Four synthetic values absent from serialization | Full path/context anonymization |
| Clean text | `test_clean` | Empty findings without gaps | Absence of all possible secrets |
| Symlink/format | `test_symlink_and_unsupported` | Two coverage gaps | Parent races, hardlinks or full permission matrix |
| Size/encoding/NUL | `test_size_encoding_and_binary` | Three files produce gaps | Every decoding/permission failure |
| File limit | `test_file_limit` | `file_count_limit` occurs | Aggregate resource ceiling |
| CLI | `test_exit_codes_and_invalid_policy` | Codes 0/1/2, empty marker, zero limit | Every malformed policy or stdout failure |

## CI evidence

[Run 38153720204](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38153720204): nine tests passed for `ubuntu-latest`, `windows-latest`, `macos-latest` at head `540e1124cd2ad35f08234df589a2f07af3357dce`. Code was then merged as `6347596d5ce6e13fe3692fdcb0bf58a9fb7ceea4`.

This establishes a specific test suite on hosted runners. It does not replace user-environment testing, corpus accuracy measurement or real-document operational validation. Every new support claim must add a test and result to this matrix.

---

[Documentation index](index.md) · [Русский](../ru/check-matrix.md)

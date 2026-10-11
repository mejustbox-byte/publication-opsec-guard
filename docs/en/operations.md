# Operations and troubleshooting

## Open-source documentation

Inspect a dedicated documentation directory. Guard source and rule documentation contain synthetic indicators for tests and explanations: inspecting the entire repository naturally produces findings. This does not establish a real leak. Do not introduce global ignoring simply to obtain a green result; the current version has no allowlist.

Inspect binary applications and attachments separately: text support does not cover an address in a screenshot or author metadata in an Office document.

## Configuration shared with a contractor

Remove secrets manually first and prepare a copy. Inspect the copy using a local naming policy; review the report and source context. Regexes do not understand an API token lacking a recognized private-key header. Guard does not replace specialist secret discovery.

## Pipeline integration

Example shell step from the repository root:

```bash
python3 guard.py prepared-materials --policy policy.local.json > report.json
```

Most CI shells fail a step on a nonzero exit code. Code 1 requires finding review; code 2 requires coverage/input review. Do not append `|| true` merely to continue publication. To retain a report after failure, configure a later artifact-retention step and preserve the original inspection exit code.

The supplied `Tests` workflow tests the product; it **does not automatically inspect every consumer's material**. There is no shipped composite Action or pre-commit hook yet. Do not execute untrusted PR code with secrets or privileges merely to add this step.

## Troubleshooting

| Symptom | Likely cause | Check and response |
|---|---|---|
| Code 2 and nothing inspected | Empty scope or excluded/unsupported objects only | Inspect `empty_scope`, `exclusions` and target path |
| `.env` produces findings | Exact filename is now supported | Review the source; retain policy outside the tree |
| Text file skipped | Limits, permissions, encoding or NUL | Read `reason` and prepare a suitable copy |
| Marker absent | Misspelled field, alternate representation, policy encoding | Check `markers`, literal text and a local example |
| Excessive findings | Short markers, educational examples, repeated values | Refine scope and policy; assess each category |
| Windows JSON paths behave unexpectedly | Escaping changes raw text | JSON semantic analysis is not implemented |
| Report appears inside input | Shell redirection created it before traversal | Store the report elsewhere and rerun |

## Decision rule

Evaluate coverage adequacy first, then finding content. Retain tool version, exact command and a private input copy in your workflow. Share only prepared, reviewed material; a Guard report is not itself authorization to disclose information.

---

[Documentation index](index.md) · [Русский](../ru/operations.md)

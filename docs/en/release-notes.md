# Alpha 0.2.0a1 status

## Changes in 0.2.0a1

- Exact `.env` support and strict UTF-8 policy with size/marker limits.
- Aggregate read, finding and directory budgets; cached newline positions.
- Contract 0.2: effective limits, counters, stop state and explicit exclusions.
- Empty scope and excluded directories no longer produce clean coverage.
- 22 regression tests; bilingual CLI, migration and resource-limit documentation.
- These budgets do not guarantee bounded total process memory or execution time.


## Code contents

Five UTF-8 text checks: RFC1918 IPv4, `.local`/`.internal` domains, home paths, private-key headers and literal policy markers. JSON contains hidden matches and recorded gaps. Input files are unchanged; inspection makes no network calls.

## Earlier baseline verification

Nine tests passed in [CI 38153720204](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38153720204) on Linux, Windows and macOS with Python 3.13. Tested head: `540e1124cd2ad35f08234df589a2f07af3357dce`; merge: `6347596d5ce6e13fe3692fdcb0bf58a9fb7ceea4`. The matrix explains each test's evidentiary limits.

## Known limitations

- No PDF/Office/OCR, images, archives, EXIF or Git history.
- No IPv6, comprehensive token discovery, key-activity checks or automatic repair.
- No complete protection from concurrent tree replacement or hardlinks.
- No installer/pip package/composite Action or full OS/CPU compatibility matrix.

## Documentation change

Documentation now separates actual implementation from plans: navigation, step-by-step examples, rule catalog, CLI/policy, JSON, troubleshooting, threats, ADR, tests and milestones. Future-capability commands are not presented as available.

## Release status

Code is in the public repository; the GitHub alpha release is prepared as a draft. A release-notes file does not imply a published release. Close the listed development-plan limitations before relying on it as the sole publication control.

---

[Documentation index](index.md) · [Русский](../ru/release-notes.md)

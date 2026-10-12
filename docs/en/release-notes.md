# CI/pre-commit integration update

Delivered composite Action, explicit-directory hook, safe Action runner and synthetic integration checks. Codes 1/2 fail the gate; Action retains a JSON report outside scope and does not overwrite existing files. Tool version remains 0.2.0a3, contract 0.2; scanner rules are unchanged. Specialist adapter remains unimplemented. See [integration guide](integrations.md).

# Alpha 0.2.0a3: installable CLI

Wheel packaging, two console commands, bundled schema data, optional validation dependencies and clean-environment installation checks are delivered. Scanner-only installation remains dependency-free. Source launchers require the adjacent package. Contract remains 0.2. Build verification compares two wheel hashes at fixed epoch; independent cross-platform reproducibility and PyPI publication are not claimed. See [installation](installation.md).

# Alpha 0.2.0a2: report validation

## Delivered

- Bundled Draft 2020-12 response schema covering report and startup-error envelopes.
- Optional offline validator with cross-field consistency and scanner-preserving codes 0/1/2; invalid/unavailable validation returns 3.
- Strict UTF-8 JSON loader: duplicate keys, non-JSON constants, symlinks, special files, size and depth limits.
- Safe capped diagnostics, 15 labeled synthetic responses, 15 validator tests and automated documentation checks.
- Detailed Russian/English integration, installation, examples, troubleshooting and limitations.

The report version remains 0.2 because its shape is unchanged. Tool version is 0.2.0a2. The scanner behavior is unchanged from a1 apart from the exposed tool version. Full tests now require optional validator dependencies; scanner-only tests do not. Report validation does not authenticate source bytes or establish publication safety. No GitHub release/tag is published by these code changes.

## Current verification: 0.2.0a2

All 37 test methods, `pip check` and `check_docs.py` passed on Linux, Windows and macOS with Python 3.13 in [run 38156874002](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38156874002) at implementation/documentation head `5fb0da0e6f67e2898b4cb1877cb68ae76a0e8f9b`. The run verifies dependency installation, 17 RU/EN page pairs and executable examples; it does not establish Intel Mac compatibility or source authenticity.

## Alpha 0.2.0a1 status

### Changes in 0.2.0a1

- Exact `.env` support and strict UTF-8 policy with size/marker limits.
- Aggregate read, finding and directory budgets; cached newline positions.
- Contract 0.2: effective limits, counters, stop state and explicit exclusions.
- Empty scope and excluded directories no longer produce clean coverage.
- 22 regression tests; bilingual CLI, migration and resource-limit documentation.
- These budgets do not guarantee bounded total process memory or execution time.


### Code contents

Five UTF-8 text checks: RFC1918 IPv4, `.local`/`.internal` domains, home paths, private-key headers and literal policy markers. JSON contains hidden matches and recorded gaps. Input files are unchanged; inspection makes no network calls.

### Earlier baseline verification

Nine tests passed in [CI 38153720204](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38153720204) on Linux, Windows and macOS with Python 3.13. Tested head: `540e1124cd2ad35f08234df589a2f07af3357dce`; merge: `6347596d5ce6e13fe3692fdcb0bf58a9fb7ceea4`. The matrix explains each test's evidentiary limits.

### Known limitations

- No PDF/Office/OCR, images, archives, EXIF or Git history.
- No IPv6, comprehensive token discovery, key-activity checks or automatic repair.
- No complete protection from concurrent tree replacement or hardlinks.
- No installer/pip package/composite Action or full OS/CPU compatibility matrix.

### Documentation change

Documentation now separates actual implementation from plans: navigation, step-by-step examples, rule catalog, CLI/policy, JSON, troubleshooting, threats, ADR, tests and milestones. Future-capability commands are not presented as available.

### Release status

Code is in the public repository; the GitHub alpha release is prepared as a draft. A release-notes file does not imply a published release. Close the listed development-plan limitations before relying on it as the sole publication control.

### Previous hardening verification

All 22 tests passed on Linux, Windows and macOS with Python 3.13 in [run 38155720812](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38155720812) at implementation head `197f07d563b25193c86ab011e8bfd0798e005bc1`. Documentation links, language parity and the user-guide example were checked locally.

---

[Documentation index](index.md) · [Русский](../ru/release-notes.md)

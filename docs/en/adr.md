# Architecture decision records

Each decision describes context, choice and consequences. Status refers to the current text alpha, not future tools in the portfolio.

## ADR-001 — Python standard library

**Status:** accepted for 0.2.0a1.

**Context:** a portable CLI needs text reading, regexes, IP validation and JSON. A complex service runtime is unnecessary.

**Decision:** use `argparse`, `pathlib`, `os`, `re`, `ipaddress`, `json` and `unittest`, with no third-party core dependencies. CI runs on Python 3.13.

**Alternatives:** Go would simplify single-binary distribution but add a separate stack; a web service would require document transfer, authentication and storage. Neither provides necessary value for this scope.

**Consequences:** users need Python; a wheel is available from 0.2.0a3; there is no native binary or installer. No third-party dependencies does not establish absence of runtime or code defects.

## ADR-002 — local reading without repair

**Status:** accepted.

**Context:** material may contain secrets; automatic replacement could corrupt technical documentation.

**Decision:** open files read-only, make no external API submissions and leave edits to the author working on a copy.

**Consequences:** no automatic sanitization or undo. Filesystem protection is limited to ordinary process controls; isolated copies remain required for untrusted trees.

## ADR-003 — JSON with hidden matches

**Status:** accepted.

**Context:** automated consumers need a report that does not duplicate discovered secrets.

**Decision:** emit JSON with relative paths and line numbers, omitting raw matches. Policy is JSON with literal markers.

**Consequences:** investigation requires local source-copy access; paths can disclose information. HTML, SARIF and localized runtime messages are not shipped. A bundled JSON Schema and optional validator are delivered in 0.2.0a2.

## ADR-004 — coverage errors separate from findings

**Status:** accepted.

**Context:** unsupported files cannot be classified safe; read errors should not hide other results.

**Decision:** retain `coverage_gaps`; return 1 for findings, otherwise 2 for incomplete coverage, otherwise 0. File-count exhaustion stops traversal.

**Consequences:** consumers must read JSON rather than only the exit code. Intentional exclusions are separate records and make coverage incomplete; empty input records `empty_scope`.

## ADR-005 — validate parsers before adding formats

**Status:** proposed; not implemented.

**Context:** PDF/Office/ZIP introduce complex parsing, archive paths, decompression bombs and attachment coverage risks.

**Decision:** define limits, extracted sections, unsupported cases and tests before adding a format. Do not expand the extension list without actual content handling.

**Consequences:** binary-document support waits for verifiable implementation, preserving truthful text-alpha results.

## ADR-006 — optional standards-based report validation

**Status:** accepted for 0.2.0a2.

**Context:** structural types are insufficient for coverage and budget consistency. Reimplementing the complete JSON Schema language would add unnecessary maintenance risk.

**Decision:** keep the scanner dependency-free; use optional `jsonschema==4.26.0` with pinned transitive versions for Draft 2020-12 validation. Bundle all schema references locally and deny network retrieval. Apply producer-specific cross-field invariants separately. Validator exit codes preserve scanner meaning; malformed or unavailable validation returns 3.

**Alternatives:** hand-maintained shape checks could drift from the published schema; structural validation alone would permit contradictory counters. A hosted validator would unnecessarily transfer reports.

**Consequences:** validator installation needs dependencies and an intact schemas directory. Validation does not authenticate the producer or authorize publication. Full tests/CI install the optional environment; scanner-only tests remain `python3 -m unittest test_guard -v`.

---

[Documentation index](index.md) · [Русский](../ru/adr.md)


## ADR-007 — installable offline CLI

Accepted for 0.2.0a3. Use setuptools with explicit packages and console entry points; retain source launchers. Bundle schema data separately and keep validator dependencies optional. Build twice at a fixed epoch and test installation outside the checkout. This adds packaging evidence, not PyPI publication or fully hash-locked builds. See [installation](installation.md).


## ADR-008 — explicit-scope publication gates

Accepted. A composite Action runs checked-in Python through literal environment inputs and retains a new external report. A pre-commit hook scans an explicit directory with pass_filenames disabled and always_run enabled. Both propagate nonzero status. External secret engines remain a separate adapter decision; they are not silently optional successful checks. See [integrations](integrations.md).

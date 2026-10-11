# Architecture decision records

Each decision describes context, choice and consequences. Status refers to the current text alpha, not future tools in the portfolio.

## ADR-001 — Python standard library

**Status:** accepted for 0.1.0a1.

**Context:** a portable CLI needs text reading, regexes, IP validation and JSON. A complex service runtime is unnecessary.

**Decision:** use `argparse`, `pathlib`, `os`, `re`, `ipaddress`, `json` and `unittest`, with no third-party core dependencies. CI runs on Python 3.13.

**Alternatives:** Go would simplify single-binary distribution but add a separate stack; a web service would require document transfer, authentication and storage. Neither provides necessary value for this scope.

**Consequences:** users need Python; there is no binary, pip package or installer. No third-party dependencies does not establish absence of runtime or code defects.

## ADR-002 — local reading without repair

**Status:** accepted.

**Context:** material may contain secrets; automatic replacement could corrupt technical documentation.

**Decision:** open files read-only, make no external API submissions and leave edits to the author working on a copy.

**Consequences:** no automatic sanitization or undo. Filesystem protection is limited to ordinary process controls; isolated copies remain required for untrusted trees.

## ADR-003 — JSON with hidden matches

**Status:** accepted.

**Context:** automated consumers need a report that does not duplicate discovered secrets.

**Decision:** emit JSON with relative paths and line numbers, omitting raw matches. Policy is JSON with literal markers.

**Consequences:** investigation requires local source-copy access; paths can disclose information. HTML, SARIF, JSON Schema and localized runtime messages are not shipped.

## ADR-004 — coverage errors separate from findings

**Status:** accepted.

**Context:** unsupported files cannot be classified safe; read errors should not hide other results.

**Decision:** retain `coverage_gaps`; return 1 for findings, otherwise 2 for gaps, otherwise 0. File-count exhaustion stops traversal.

**Consequences:** consumers must read JSON rather than only the exit code. Intentional exclusions are not gaps and must be interpreted through scope and documentation.

## ADR-005 — validate parsers before adding formats

**Status:** proposed; not implemented.

**Context:** PDF/Office/ZIP introduce complex parsing, archive paths, decompression bombs and attachment coverage risks.

**Decision:** define limits, extracted sections, unsupported cases and tests before adding a format. Do not expand the extension list without actual content handling.

**Consequences:** binary-document support waits for verifiable implementation, preserving truthful text-alpha results.

---

[Documentation index](index.md) · [Русский](../ru/adr.md)

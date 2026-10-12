# Validation of all response formats

## Supported envelopes

The existing `publication-opsec-validate REPORT` now dispatches core response-0.2 (including its startup error), historic documents-0.1, documents-0.2, secrets-0.1 and bundle-0.1. Install the optional validation dependencies. Core scanner/dispatch does not require them. Strict UTF-8 JSON loading, duplicate/constant rejection, byte/depth/error caps and network-denied schema retrieval remain in force. Output errors contain codes and safe locations, not input values.

## Shape and consistency

Every envelope uses a bundled Draft 2020-12 schema with local references. Documents enforce coverage/gap agreement, nonempty completed scope, part/XML/finding budgets and finding asset consistency. Secrets validate their core child, completed/reason agreement, completed scope and no findings for an unfinished engine. Bundle validates each child, requested-engine state, aggregate coverage, nonempty scope and file/byte/document/finding limits. Core checks are unchanged.

Valid reports return their inspection code 0/1/2; structurally or semantically inconsistent input and missing runtime/schema return 3. A valid startup-error response still returns 2. Validation checks declarations: fabricated but internally consistent provenance can pass; signatures, file hashes and source identity are not verified. Schema alone does not implement cross-field rules. Old consumers must not silently treat an unknown envelope as clean.

## Integration and tests

Run after the scan, keeping its original status. For mixed bundles inspect child states and global gaps. Tests cover all envelope types, invalid nested reports, contradicted coverage/budgets, absent requested engines and safe diagnostics. Existing loading/no-network tests remain. Runtime failure is not a fallback to success. Schema files are included in the wheel.

---

[Documentation index](index.md) · [Русский](../ru/all-report-validation.md)

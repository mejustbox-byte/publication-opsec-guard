# Security and data handling

## Before execution

Use an isolated material copy, not a live directory writable by an untrusted process. Administrator execution is unnecessary; use an account limited to the prepared copy. Hardlinks can reference sensitive data and are not separately detected.

Do not raise limits without evaluating input size. The scanner accumulates findings; multiple large match-heavy files can use substantial memory. OS/container resource limits may provide additional controls but are not part of this distribution.

## Local data

Guard does not send documents, markers or results over the network. Repository download and GitHub Actions are separate development operations. If you upload reports as CI artifacts, the CI service receives them; that is your pipeline decision.

Evidence omits match values. Paths, line numbers, categories and counts remain. Keep reports and policies private; do not commit actual `policy.local.json` to public Git. `.gitignore` helps ordinary staging but does not prevent forced commits or issue disclosure.

## Key material

A private-key header requires source-context review. Never place the key body in a public issue. Real exposed keys require revocation/replacement outside Guard. External key-validity checks are not implemented.

## Reporting a problem

Reproduce using synthetic input. Include tool version, OS, command without sensitive paths, expected and observed behavior. Do not attach real keys, production exports or internal names.

Use a repository private vulnerability channel only if it is actually available. Enabled private vulnerability reporting has not been confirmed; a public issue containing secrets is unacceptable. No response SLA or dedicated support service is claimed.

## Security limitations

This alpha is a preliminary text inspector. It is not DLP, a sandbox, a comprehensive secret scanner or an automatic publication-approval system. The threat model and rule catalog detail limits; the material owner must supplement the technical control with review.

---

[Documentation index](index.md) · [Русский](../ru/security.md)

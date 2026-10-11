# Threat model

Secrets and infrastructure disclosure in documents; untrusted files; symlink escape; report leakage.

Assets: inputs, evidence, local policy and reports. Trust boundaries: input → parser → normalized model → checks → export. Controls: size limits, no content execution, evidence sanitization, no network calls by default. Residual risk: format coverage gaps and false positives; ambiguous results require review.

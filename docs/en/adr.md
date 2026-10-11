# ADR-001

Status: proposed; accepted for the initial text prototype. Python standard library for a portable CLI; JSON instead of YAML in the core; unittest for tests. This reduces dependencies and preserves offline execution. Alternatives: Go simplifies binary distribution but complicates reuse of Python integrations; a web service introduces sensitive-data transfer and is unnecessary for MVP. Runtime and external tool versions must be verified against official sources before CI pinning. Other projects confirm this decision after existing code inspection.

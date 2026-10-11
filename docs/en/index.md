# Publication OPSEC Guard documentation

> **Implementation:** 0.2.0a2 · **Report contract:** 0.2 · **Status:** text-only alpha prototype.

Publication OPSEC Guard inspects prepared material before it leaves an organization. It reads local UTF-8 files, checks five disclosure categories and returns JSON with finding locations. It does not modify input material or send it to external services.

## Choose your path

| Goal | Document | What you learn |
|---|---|---|
| Understand purpose and boundaries | [Requirements](requirements.md) | Supported tasks and excluded capabilities |
| Run a first inspection | [User guide](user-guide.md) | Commands, a synthetic example and repeat inspection |
| Configure execution | [CLI and policy](cli-reference.md) | Exact arguments, limits and exit codes |
| Investigate a finding | [Rule catalog](rule-catalog.md) | Algorithms, examples, limitations and response |
| Integrate a report consumer | [JSON contract](report-format.md) | Fields, types and coverage-gap reasons |
| Validate an incoming report | [Report validation](report-validation.md) | Schema, consistency, exit codes and safe integration |
| Operate the tool | [Operations and troubleshooting](operations.md) | Inspection workflow, errors and CI use |
| Assess the tool's own security | [Threat model](threat-model.md), [Security](security.md) | Trust boundaries, residual risks and data handling |
| Understand implementation | [Architecture](architecture.md), [ADR](adr.md) | Data flow and technical decisions |
| Review quality evidence | [Matrix](check-matrix.md), [Testing](testing-lab.md) | What has been tested and what tests do not establish |
| Plan development | [Plan](development-plan.md), [Release notes](release-notes.md) | Upcoming milestones and actual alpha limitations |
| Contribute a change | [Contributing](contributing.md) | Updating rules, contracts and both document versions |

## Reading status labels

**Implemented** means behavior exists in the scanner or validator. **Verified** means a named test or specific CI run supports the claim. **Planned** means a future requirement, not an available command.

A `fail` finding identifies a disclosure indicator, not a confirmed incident. `not_tested` identifies a coverage gap. No findings does not eliminate the need to review gaps and make a publication decision.

All examples are synthetic. Production exports, secrets, internal organization names and real logs are unnecessary to reproduce them.

---

[Documentation index](index.md) · [Русский](../ru/index.md)

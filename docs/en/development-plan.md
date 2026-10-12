# Development plan and acceptance gates

## Current state

The 0.2.0a4 text alpha has five rules, contract 0.2 and 50 test methods. M1–M5 are implemented. M2 delivers a bundled schema, standalone validator, labeled response fixtures and automated bilingual-document checks; M6 remains planned.

## Milestones

| Milestone | Work | Reviewable output | Completion gate |
|---|---|---|---|
| M1: implemented | Explicit UTF-8 policy, strict fields, exact `.env`, aggregate limits | CLI and regression tests | Policy typos are not silent; exhausted limits produce gaps, not success |
| M2: implemented | Versioned schema, explicit exclusions and empty-input handling | Schema, validator, updated RU/EN examples | Consumer distinguishes startup error, empty scope and result |
| M3: implemented | Positive/negative/boundary cases per ID | Labeled synthetic corpus | Every claimed representation has a test; measurements are published without inflation |
| M4: implemented | CLI packaging, fixed dependencies, reproducible build | Installation artifact and guide | Installation verified in a clean environment; report exposes version |
| M5: implemented | CI example, pre-commit, specialist secret-scanner adapter | Failure/missing-engine tests | External engine failures remain visible; raw secrets are not emitted |
| M6: documents | One format per subcycle after a justified selection | Parser, limits, corpus and threat model | Unsupported attachments and failures remain visible |

## Complete-cycle order

Requirements and scope → ADR and threat model → implementation → tests → documentation/public-artifact review → PR → CI at exact head → merge → release with limitations. An unfinished gate is not replaced by success of an earlier one.

## Definition of Done

- Behavior is described in both languages and matches code.
- Positive and negative tests exist; data handling includes invalid input.
- Examples contain no actual secrets or production exports.
- Contract changes include versioning and migration instructions.
- CI is verified at a specific SHA; examples execute and links resolve.
- Release notes describe actual delivery and residual limitations.

## Dependencies and risks

Specialist secret discovery requires engine, license, version and credential-validation policy decisions before integration can be claimed. Binary formats require extraction/parser limits. Hosted macOS CI does not establish compatibility with every Intel Mac; that requires evidence on the relevant architecture.

## Portfolio queue

After this project completes, the next independent cycle covers a shared OPSEC report contract, followed by a validation lab, recovery audit, network audit and Detection Readiness. Existing auditors integrate after their actual formats are inspected. This plan does not imply background execution or automatically created resources.

---

[Documentation index](index.md) · [Русский](../ru/development-plan.md)


M3 delivered: [54 labeled rule cases](rule-corpus.md), 50 test methods locally. Distribution and integrations are delivered; binary-format handling remains planned.


M5 integration gate: Action, hook and pinned adapter implemented; actual-engine verification is Linux-only. See [integration guide](integrations.md).


[Pinned secret adapter](secret-adapter.md) delivered in 0.2.0a4. This supersedes the earlier planned-adapter status. Binary-document handling remains planned.

# Threat model

## Protected assets

Guard helps reduce publication disclosure. It also processes untrusted material, so execution and its output are within the threat model. Assets include source documents, local markers, identifying paths, machine availability and result integrity.

## Actors and assumptions

A material author may accidentally retain working values. An untrusted supplier may provide special files, symlinks or match-heavy input. A report recipient may see a filename even when matched values are hidden.

Assume execution on an isolated copy with access limited to necessary users. The tree should not change concurrently during inspection. Compromised OS or Python runtime is outside the tool's protection.

## Scenarios

| ID | Threat | Existing control | Residual risk |
|---|---|---|---|
| TM-01 | Address/domain disclosure | PUB-001/PUB-002 | Unsupported representations and zones are missed |
| TM-02 | User/key disclosure | PUB-003/PUB-004 | No comprehensive secret detector; a header does not prove a real key |
| TM-03 | Project-name disclosure | PUB-005 | Requires correct local policy |
| TM-04 | Input points outside the tree | Symlinks skipped; available `O_NOFOLLOW` | Parent replacement and hardlinks are not fully prevented |
| TM-05 | Memory/CPU exhaustion | Per-file and file-count limits | Total memory and finding count lack separate bounds |
| TM-06 | Disclosure through reports | No raw match in evidence | `asset_id`, counts and rule names remain |
| TM-07 | Error interpreted as success | `coverage_gaps`, code 2 without findings | Code 1 can also include gaps; empty input returns 0 |
| TM-08 | False full-audit claim | Scope field and documented limits | A consumer may disregard limits |

## Trust boundaries

Policy is not executable code but affects match volume and may disclose organization details. A report is not trusted HTML: downstream web consumers must escape `asset_id`. Guard ships no HTML renderer.

CI runs synthetic source tests. Successful CI does not prove all user files safe or establish hostile-tree isolation.

## Risk-reduction priorities

Bound total input and findings first, then strengthen path handling and policy validation. Add formats only with a parser-specific threat model: simply reading ZIP or Office bytes does not establish support. Assess detection quality on a published synthetic corpus with negative cases.

---

[Documentation index](index.md) · [Русский](../ru/threat-model.md)

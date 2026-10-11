# Development and maintenance

## Before a change

Read requirements, rule catalog and threat model. Select a concrete defect or capability and describe observable behavior. Avoid changing rules, report format and CLI together without explaining their relationship: compatibility becomes harder to review.

## Rule changes

Add synthetic positive input and a nearby negative case. Update ID, static severity, algorithm, limitations and user response in both catalogs. Never use actual secrets for regression tests. Regex changes can increase false positives; test more than new matches.

## Interface changes

For JSON field changes, update the contract, example, consumer scenario and schema version when compatibility breaks. For argument changes, update the CLI reference and execute the guide example. Do not document a field as available before implementing it.

## Checks before a PR

```bash
python3 -m unittest discover -v
python3 guard.py --help
git diff --check
```

Also execute both synthetic-guide sequences and verify the 1 → 0 transition. Open README and Mermaid in GitHub Preview. Check local links, RU/EN page pairing and absence of production data.

## Bilingual documentation

`docs/ru` and `docs/en` share filenames and technical facts. Commands, IDs, JSON fields and versions match; explanations are translated. Translation must retain exclusions and limitations, not just the happy path. Update both pages in one PR.

## Review and release

PR descriptions explain the problem, resulting behavior, validation and residual limitations. Before merging, verify CI at the current head rather than a previous green commit. Release notes describe final delivery, omitting correspondence, assignments and approval history. Licensing is not yet defined by a separate LICENSE; a public repository must not be described as granting an MIT/Apache license.

---

[Documentation index](index.md) · [Русский](../ru/contributing.md)

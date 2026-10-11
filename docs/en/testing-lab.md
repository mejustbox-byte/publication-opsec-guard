# Product verification and reproducibility

## Quick execution

From the repository root:

```bash
python3 -m unittest discover -v
```

Expect 22 tests and `OK`. Tests use temporary directories and synthetic strings, not production infrastructure or actual secrets. The symlink test requires permission to create links; the specific Windows runner passed, but local Windows policies may differ.

## Verification layers

1. **Rules:** known indicators match; documentation and invalid addresses do not count as RFC1918.
2. **Collection:** unsupported files, symlinks, limits and text errors remain coverage gaps.
3. **CLI:** subprocess execution verifies exit codes and the short policy-error object.
4. **Platforms:** GitHub Actions executes the same suite on three hosted operating systems.
5. **Documentation:** execute the first-run example and compare actual JSON IDs/lines; check links and RU/EN pairs locally.

## Quality gaps

The current suite does not measure precision/recall. That requires a labeled positive/negative corpus, fixed rule version and TP/FP/FN/TN counts. Green CI cannot support a “100% accurate” claim.

Dedicated inaccessible-directory, path-race, hardlink, aggregate-memory, closed-pipe and individual private-key-header tests remain incomplete.

## Adding a scenario

Create synthetic input and specify the expected rule finding or gap. Add a nearby negative case to prevent overbroad matching. For regressions, describe the observed defect, add a reproducing test, then change the rule.

For OS behavior, record OS, Python, architecture, permission mode and outcome. Sanitize CLI output containing real paths before publishing. Paid cloud resources are unnecessary for this lab.

---

[Documentation index](index.md) · [Русский](../ru/testing-lab.md)

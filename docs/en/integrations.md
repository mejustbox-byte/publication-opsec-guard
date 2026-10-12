# GitHub Action and pre-commit integration

## Purpose and supplied components

`action.yml` is a composite Action that runs the scanner on an explicit prepared directory and retains a JSON report. `.pre-commit-hooks.yaml` provides a Python hook installed in a pre-commit-managed environment. Both preserve the scanner decision: 0 is no finding or recorded gap, 1 is findings (possibly with gaps), 2 is incomplete coverage or invalid input. They do not approve publication and do not discover every token type.

## GitHub Action: configure deliberately

Python 3.12+ must be available as `python3`; use setup-python before the composite Action. Paths are evaluated from the caller workspace. `directory` and `report` are required; `policy` is optional. The report path must be outside the inspected directory and must not already exist. This prevents report self-inspection and accidental overwrite. Use a separate path per matrix job or repeated invocation.

Replace `REVIEWED_COMMIT_SHA` with an inspected immutable repository commit containing this Action, not the literal placeholder. Remove `policy` if no policy is needed. Create the prepared directory before this step:

```yaml
permissions:
  contents: read
jobs:
  publication:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.13'
      - uses: mejustbox-byte/publication-opsec-guard@REVIEWED_COMMIT_SHA
        with:
          directory: prepared-materials
          policy: policy.local.json
          report: ${{ runner.temp }}/publication-opsec-report.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: publication-opsec-report
          path: ${{ runner.temp }}/publication-opsec-report.json
```

A nonzero result fails the inspection step. The `exit-code` output is recorded before the runner exits. `if: always()` retains the report after findings or coverage failures; it does not turn inspection into success. A report destination/setup failure returns 2 and may leave no report. Downstream publication should depend on the successful inspection job and a separate human assessment. Do not use `continue-on-error` or `|| true` to allow publication after a failure.

The Action prints only the exit code. JSON retains filenames and line numbers; do not treat it as safe for public artifact upload. Use access controls and retention appropriate to its paths and metadata. Inputs are read from environment variables, not interpolated into shell commands. No scanner install, secret upload or online credential verification is performed by the Action.

## pre-commit: explicit directory scope

Create `.pre-commit-config.yaml` in the consumer repository and replace the revision placeholder with a reviewed commit:

```yaml
repos:
  - repo: https://github.com/mejustbox-byte/publication-opsec-guard
    rev: REVIEWED_COMMIT_SHA
    hooks:
      - id: publication-opsec-guard
        args: [prepared-materials, --policy, policy.local.json]
```

Install pre-commit separately, then run `pre-commit install` and `pre-commit run publication-opsec-guard --all-files`. The hook environment installs the scanner package automatically; Python 3.12+ must be available. The hook emits the scanner's JSON to pre-commit output, so filenames may appear in developer logs. Keep organization policies private.

`pass_filenames: false` means the hook scans the directory from `args`, rather than receiving staged filenames. `always_run: true` prevents a clean-looking skip due only to file filters. The directory argument is mandatory. Scanning the entire repository normally includes synthetic rule examples and exclusions and may therefore fail. Select a dedicated prepared-material directory; this hook is a publication preflight, not a guarantee about all staged files. Local hooks can be bypassed; use CI as another gate.

## Tested behavior

Four subprocess test methods cover clean material, findings, unsupported format, invalid policy, report-inside-scope rejection, overwrite prevention and literal shell-looking directory names. `verify_hook.py` installs the actual hook manifest in a temporary Git repository and verifies clean/finding outcomes through pre-commit 4.3.0. CI invokes the local composite Action on synthetic clean and finding material after the full test suite. Linux, Windows and macOS run the same checks. These are synthetic integration checks, not proof of every consumer workflow.

## Specialist engine boundary

The optional [pinned Gitleaks adapter](secret-adapter.md) is delivered as a separate command in 0.2.0a4. The core Action/hook still runs only the text scanner. Add a separate adapter step when needed; an unavailable engine is not a clean result. The real engine has Linux evidence only. Guard key-header detection alone remains incomplete secret discovery.

## Troubleshooting

Code 2 with no report: check report destination, existing file, permissions and whether it is inside scope. Code 2 with a report: inspect coverage gaps or startup-error response. Hook skipped: verify the correct hook ID and consumer configuration; the supplied manifest uses always_run. Missing `python3`: configure the interpreter before running the Action. A successful gate reports only the inspected UTF-8 scope and current five rules.

Upstream references: [pre-commit configuration](https://pre-commit.com/), [Gitleaks](https://github.com/gitleaks/gitleaks).

---

[Documentation index](index.md) · [Русский](../ru/integrations.md)


[Pinned secret adapter](secret-adapter.md) delivered in 0.2.0a4. This supersedes the earlier planned-adapter status. Binary-document handling remains planned.

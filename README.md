# Publication OPSEC Guard

### Inspect text before publication

**Local · Read-only · Five rules · JSON without raw matches**

Guard locates working addresses, internal domains, user paths, private-key headers and organization markers in prepared material. It identifies files and lines, retains uninspected objects and leaves publication decisions to the information owner.

> **0.2.0a1 is a text-only alpha prototype.** PDF, Office, images, archives and Git history are not inspected. Exit code 0 does not guarantee the absence of secrets.

[Русский](README.ru.md) · [Full guide](docs/en/index.md) · [Rules](docs/en/rule-catalog.md) · [CLI](docs/en/cli-reference.md) · [Roadmap](docs/en/development-plan.md)

## The problem it solves

Before publishing a README, issue or sanitized configuration, check for retained environment details. Guard performs a repeatable preliminary inspection of a local copy. Output locates a source line without duplicating its matched value in JSON.

## Capabilities

| Rule | Detects | Purpose |
|---|---|---|
| PUB-001 | RFC1918 IPv4 | Internal addressing disclosure |
| PUB-002 | `.local` / `.internal` | Internal naming disclosure |
| PUB-003 | `/home/`, `/Users/`, Windows home paths | Identifying usernames |
| PUB-004 | Private-key headers | Possible private-key material |
| PUB-005 | Literal policy markers | Organizational names and identifiers |

## Quick start

```bash
git clone https://github.com/mejustbox-byte/publication-opsec-guard.git
cd publication-opsec-guard
python3 guard.py /path/to/prepared-text > report.json
```

Python must be installed; no third-party packages are required. Write reports **outside the inspected directory**. On Windows replace `python3` with `python` or `py -3` if needed. The [user guide](docs/en/user-guide.md) contains a reproducible example with expected results.

| Code | Meaning |
|---|---|
| 0 | No findings or recorded gaps; review file count and scope |
| 1 | Findings exist; gaps may also exist |
| 2 | Incomplete coverage without findings, or input/policy error |

## Important behavior

Files use UTF-8 and a limited extension list; JSON/YAML are not parsed semantically. `.env` files, including exact filename `.env`, are inspected. `.git` and `__pycache__` are excluded and recorded; coverage is incomplete. Raw matches are hidden, filenames remain. Total memory lacks a separate limit; use isolated copies for untrusted trees.

## Verification and documentation

All 22 tests passed in [CI](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38155720812) on Linux, Windows and macOS. The [matrix](docs/en/check-matrix.md) documents the tested implementation head and limits of this evidence.

Start with the [documentation index](docs/en/index.md): requirements, threats, architecture, ADR, rules, CLI/policy, JSON, troubleshooting, tests and milestones. [Release notes](docs/en/release-notes.md) describe actual status; the alpha release remains a draft.

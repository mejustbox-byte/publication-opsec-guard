# Purpose, requirements and boundaries

## 1. The problem

Material prepared for READMEs, issues, presentations and contractors can retain details of real environments: IP addresses, internal domains, home directory paths or organizational terms. Such details may reveal infrastructure even without a password. A private key appearing in text is a separate risk category.

Guard performs a preliminary inspection of a material copy. Its output locates content for review and explains which files could not be inspected. The information owner retains the publication decision.

## 2. Users and use cases

| User | Input | Practical goal |
|---|---|---|
| Open-source maintainer | Documentation and examples directory | Find real values before committing |
| System administrator | Sanitized text export copy | Check for remaining environment addresses and names |
| Security engineer | Report or issue material | Locate indicators without printing matched values |
| CI developer | Prepared directory and local policy | Stop a pipeline on findings or incomplete coverage |

Do not inspect an entire home directory to review one document: it expands scope and creates a large report containing identifying paths.

## 3. Implemented functional requirements

| ID | Requirement | Actual behavior |
|---|---|---|
| FR-01 | Inspect a local directory | One required `directory` argument; root symlink rejected |
| FR-02 | Bound each file read | Reads up to `max_bytes + 1` bytes to detect oversize files |
| FR-03 | Five indicator classes | PUB-001–PUB-005; exact behavior in the rule catalog |
| FR-04 | Hide raw matches | Evidence retains line number and `redacted: true` |
| FR-05 | Account for uninspected objects | `coverage_gaps` records skip reasons; gaps are not passes |
| FR-06 | Machine-readable output | JSON on stdout and exit codes 0/1/2 |
| FR-07 | Organization policy | Optional JSON list of literal `markers` |

## 4. Nonfunctional properties and limitations

The core uses Python's standard library and needs no third-party packages. Inspection does not make network calls or repair files. File and directory names are sorted for predictable traversal.

Defaults: 2,000,000 bytes per file, 10,000 encountered files, 50,000,000 total bytes read, 10,000 findings and 10,000 directories. These limits do not bound total process memory or runtime: `os.walk` enumerates immediate directory entries before checking fanout, and report/path lists remain in memory.

Report paths are relative to the root. They may remain sensitive despite hidden matches. Describing the current output as fully anonymized would be inaccurate.

## 5. Support

Supported extensions: `.txt`, `.md`, `.rst`, `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.conf`, `.csv`, `.py`, `.ps1`, `.sh`, `.xml`, `.html`, `.env`; exact filename `Dockerfile` is recognized separately. YAML, JSON and HTML are inspected as text, not parsed semantically. Exact `.env`, `settings.env` and `Dockerfile` are supported.

`.git` and `__pycache__` are recorded in `exclusions` and make coverage incomplete. Git history is not inspected.

Unsupported: PDF, Office, images, OCR, archives, EXIF, IPv6, key validity and comprehensive token discovery. Tests have passed on Linux/Windows/macOS hosted runners; this does not establish every OS version, CPU architecture or network-filesystem scenario.

## 6. Alpha acceptance and future acceptance

The alpha must detect synthetic indicators for five rules, omit their values from evidence and retain coverage gaps. The current regression tests establish part of this behavior.

A broader release still needs individual negative cases for every rule, inaccessible-directory testing, total-memory bounds, adversarial-tree tests. A green baseline CI does not establish those requirements.

---

[Documentation index](index.md) · [Русский](../ru/requirements.md)

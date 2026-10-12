# Installation, build and distribution

## What is delivered

Version 0.2.0a4 supplies a Python wheel/source build configuration and two console commands: `publication-opsec-guard` scans text; `publication-opsec-validate` validates saved JSON. The scanner has no runtime dependencies. Validation is an optional extra with the same exact versions as `requirements-validation.txt`. The wheel includes the schema in a dedicated data package. Tests, examples and source wrappers remain in the checkout/source distribution rather than the runtime wheel.

## Requirements and supported evidence

Python 3.12 or newer is required by package metadata. CI uses Python 3.13 on Linux, Windows and macOS; local checks use 3.12. A platform-independent wheel contains Python code, not native scanner binaries. Optional dependencies may need compatible native wheels. This does not prove every OS/CPU combination, including each Intel Mac.

## Install from a reviewed checkout

Use a separate virtual environment to avoid changing system Python. From the cloned repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/publication-opsec-guard /path/to/prepared-text > report.json
```

On Windows use `python` or `py -3` for environment creation, `.venv\Scripts\python.exe` for pip and `.venv\Scripts\publication-opsec-guard.exe` for the command. No activation is necessary when invoking explicit paths. Keep `report.json` outside the inspected directory.

For validation install the optional extra:

```bash
.venv/bin/python -m pip install '.[validation]'
.venv/bin/publication-opsec-validate report.json
.venv/bin/python -m pip check
```

Installation may download build tools and optional dependencies; scanning and report validation do not access the network. Core wheel installation can use `--no-index --no-deps` with a previously built local wheel. This repository is not a published PyPI package: do not assume a bare package-name install retrieves this product.

## Build and verify

Build tools are pinned in `pyproject.toml`: setuptools 84.0.0 and wheel 0.48.0. Install them in a build environment, then build locally:

```bash
python3 -m pip install setuptools==84.0.0 wheel==0.48.0
python3 -m pip wheel --no-build-isolation --no-deps --wheel-dir dist .
python3 verify_install.py
```

`verify_install.py` builds twice using fixed `SOURCE_DATE_EPOCH`, compares SHA-256 of wheel bytes, installs into a fresh environment outside the repository, checks scanner codes 0/1/2 and validator code 3 without optional dependencies, installs the pinned validation environment and verifies a saved clean report. It tests wheel data loading rather than accidentally importing the checkout. CI retains built wheels as artifacts after this verification.

Equal wheel bytes in one environment demonstrate repeatability under those conditions; this is not a claim of independent reproducible builds across all platforms. Version pins are not a hash-locked dependency supply chain or vulnerability audit. Do not publish build directories containing local data.

## Compatibility and removal

`python3 guard.py` and `python3 validate_report.py` remain compatibility launchers. They now require the adjacent `publication_opsec_guard` package: copying only a launcher is insufficient. The report schema remains 0.2; `tool_version` becomes 0.2.0a3. To remove an installation use the environment's pip uninstall or delete the dedicated virtual environment. Inputs and saved reports are not changed by uninstalling.

## Troubleshooting

Missing console command usually means the wrong environment or PATH; invoke its full path. A validator `dependency_missing` result returns 3 until the optional dependencies are installed. `validation_unavailable` requires checking the packaged schema and environment integrity. Build-tool downloads failing do not imply the scanner inspected anything. Installation success does not establish publication safety.

---

[Documentation index](index.md) · [Русский](../ru/installation.md)


[Optional secret-engine CLI](secret-adapter.md) is installed with the same package; the engine binary is supplied separately.


[DOCX console command](docx-inspection.md) is supplied in 0.2.0a5 without extra runtime dependencies.

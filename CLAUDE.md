# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project actually is

The **Python CLI is the real, shipped product**. Everything under `src/portchecker/`
is the source of truth. The Swift menu bar app (`swift/`) is a **non-building stub**
— see `swift/CLAUDE.md`. Do not treat Swift work as equivalent in maturity to the
Python CLI.

There is also `PortCheckerMenuBarPy/` — a **working** Python/py2app menu bar app
(wired to `make build-pyapp`). Unlike the Swift stub, this one actually builds and
is the realistic "menu bar app" option today if that surface needs work.

## Real build/test/lint commands (verified against Makefile)

```
make install-dev   # venv + pip install -e ".[dev]" + pyinstaller/py2app
make install       # venv + pip install -e .
make test          # pytest tests/ -v --cov=src/portchecker --cov-report=term-missing
make lint          # ruff check src/portchecker && mypy src/portchecker
make format        # black src/portchecker tests && ruff check --fix src/portchecker
make run ARGS=...  # python -m portchecker $(ARGS), defaults to `scan`
make help-cli      # python -m portchecker --help
make dev           # format + run scan
make build         # ./scripts/build.sh — full build (CLI + apps)
make build-cli     # pyinstaller onefile -> dist/portchecker
make build-pyapp   # py2app build of PortCheckerMenuBarPy -> dist/Port Checker (Python).app
make build-swiftapp # xcodebuild the Swift app — WILL FAIL, see below
```

Entry point: `portchecker = "portchecker.cli:app"` (Typer app), package installed
from `src/` via setuptools (`pyproject.toml`).

## Duplicate Swift source trees — confirmed

Two copies of the Swift menu bar app exist:

- `PortCheckerMenuBar/` (repo root, mtimes ~Jan 16) — **older, smaller** (4 files,
  no `Info.plist`, no `ServiceDetailView.swift`/`SettingsView.swift`). **Stale
  duplicate — do not edit this one.**
- `swift/PortCheckerMenuBar/` (mtimes ~Jan 31, later) — newer, more complete
  (adds `Info.plist`, `ServiceDetailView.swift`, `SettingsView.swift`, xcassets,
  a `Resources/` dir with the CLI binary copied in). This is the tree referenced
  by `make build-swiftapp`. **If Swift work is ever needed, edit here.**

Neither tree has a committed `.xcodeproj` — see `swift/CLAUDE.md`.

## Dead code check

`portchecker_old.py` does **not** exist at the repo root (checked directly) — a
prior finding flagging it as dead code was stale/incorrect. Only
`portchecker_build.py` and `portchecker_entry.py` are present at root, both
actively referenced by the Makefile/PyInstaller spec.

## Python version — real mismatch found

`pyproject.toml` declares `requires-python = ">=3.10"` (matches `black`/`mypy`/
`ruff` `target-version = py310`), and the source already uses 3.10+ syntax
(PEP 604 unions, e.g. `Dict | None`, `str | None` in `config.py`/`scanner.py`) —
this is internally consistent and correct.

However **`README.md` line 223 says "Python 3.9+ (for CLI)"**, which is wrong and
would produce a `SyntaxError` on 3.9 given the union syntax already in use. Treat
`pyproject.toml` as authoritative; the README needs a fix (not done here — out of
scope for this pass).

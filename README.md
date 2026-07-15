# Port Checker

Port Checker finds TCP ports listening on your Mac, shows which process owns
each port, checks basic exposure risks, and can stop development services.

## Current status

| Part | Status | Notes |
| --- | --- | --- |
| Python CLI | Primary, working | Source of truth: `src/portchecker/`. Requires Python 3.10+ and macOS `lsof`. |
| Native SwiftUI app | Buildable development app | SwiftPM target for macOS 14+. Bundles the CLI. Locally ad-hoc signed; no installer or published release. |
| Python menu bar app | Fallback | py2app build for macOS. Less developed than the CLI. |

No Homebrew formula, downloadable GitHub release, or App Store build currently
exists. Build from this checkout.

## Easiest setup

Need:

- macOS
- Python 3.10 or newer (`python3 --version`)
- `make`
- `lsof` (included with macOS)

Open Terminal. Go to this project folder, then run:

```bash
cd /path/to/portchecker
make install
make run
```

Replace `/path/to/portchecker` with actual folder path. First command creates
`venv/` and installs Port Checker there. Second command scans listening ports.

After setup, use either style:

```bash
# Short Makefile form
make run ARGS="scan"

# Direct CLI form
./venv/bin/portchecker scan
```

## Everyday use

### See running services

```bash
./venv/bin/portchecker scan
```

Output gives each visible service an ID. IDs are recalculated on every scan.

### Check common development ports

```bash
./venv/bin/portchecker check 3000 5173 8000 8080
```

### Stop one service safely

First scan, find service ID, then stop it:

```bash
./venv/bin/portchecker scan
./venv/bin/portchecker stop 1
```

Port Checker shows target and asks for confirmation. Use PID when needed:

```bash
./venv/bin/portchecker stop --pid 12345
```

`--yes` skips confirmation. `--force` sends an immediate force kill. Use both
only when target process is known.

### Check network exposure

```bash
./venv/bin/portchecker exposed
./venv/bin/portchecker security
```

These are local heuristics, not a full security audit.

### Save favorite ports

```bash
./venv/bin/portchecker fav-add 3000 "Frontend" --note "Local web app"
./venv/bin/portchecker fav-list
./venv/bin/portchecker fav-status
./venv/bin/portchecker fav-stop "Frontend"
./venv/bin/portchecker fav-remove "Frontend"
```

Favorites live in `~/.config/portchecker/favorites.json`.

### JSON for scripts

```bash
./venv/bin/portchecker scan --json
./venv/bin/portchecker scan --json --external
./venv/bin/portchecker security --json
./venv/bin/portchecker fav-list --json
```

Full command list:

```bash
make help-cli
./venv/bin/portchecker COMMAND --help
```

## Native macOS app

Need macOS 14+ and Xcode with Swift 6 support.

```bash
make install-dev
make build-swiftapp
open "dist/Port Checker.app"
```

Build flow creates standalone CLI, compiles Swift package, bundles CLI into app,
and ad-hoc signs local app. Output: `dist/Port Checker.app`.

App provides dashboard, menu bar view, favorites, settings, exposure indicators,
service details, and guarded process stopping. App uses same CLI and favorites
file as terminal commands.

## Python menu bar fallback

```bash
make install-dev
make build-pyapp
open "dist/Port Checker (Python).app"
```

Output: `dist/Port Checker (Python).app`. Full Xcode app not required.

## Developer setup

```bash
make install-dev
make test
make lint
```

Useful targets:

```bash
make help
make run ARGS="scan --external"
make build-cli
make build-swiftapp
make build-pyapp
make build
make clean
```

`make format` changes files. Run it only when formatting changes are wanted.

## Project layout

```text
src/portchecker/                 Python package and CLI
tests/                           Python tests
swift/PortCheckerMenuBar/        Active native SwiftUI source
Package.swift                    Native app SwiftPM manifest
script/build_and_run.sh          Native app build/run helper
PortCheckerMenuBarPy/            Python/py2app menu bar fallback
PortCheckerMenuBar/              Old stale Swift duplicate; do not edit
scripts/build.sh                 Full build helper
Makefile                         Supported setup, test, run, and build commands
```

## Limitations

- macOS only. Scanner depends on macOS `lsof` output and app targets macOS.
- Security report uses local rules and exposure checks. It does not replace a
  firewall review or network scan.
- Process stopping changes live system state. System processes are filtered and
  protected, but always verify target.
- Native app is development-distributed only: ad-hoc signed, not notarized.
- No CI workflow, package registry release, Homebrew formula, or downloadable
  release is currently committed.

## Configuration

Runtime files:

```text
~/.config/portchecker/config.json
~/.config/portchecker/favorites.json
```

Set `PORTCHECKER_CLI` to an executable path when Python menu app cannot find CLI.

## Version and licensing

Current package version: `1.0.0`. `pyproject.toml` declares MIT licensing, but
repository does not currently include a `LICENSE` file.

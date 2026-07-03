# CLAUDE.md — swift/

This is a **non-building stub**. Editing Swift files here will not produce a
testable app without additional manual setup.

## What's actually present

- Source files: `PortCheckerMenuBarApp.swift`, `MenuContentView.swift`,
  `PortScanner.swift`, `ServiceDetailView.swift`, `SettingsView.swift`
- `Info.plist`, `PortCheckerMenuBar.xcassets/`
- `Resources/` — contains a copy of the built `portchecker` CLI binary (dropped
  in by `make build-swiftapp` via `cp dist/portchecker swift/PortCheckerMenuBar/Resources/`)
- `README.md` — build instructions

## What's missing

**No `.xcodeproj` (or `.xcworkspace`) is committed anywhere in this tree.**
`make build-swiftapp` runs `xcodebuild -project PortCheckerMenuBar.xcodeproj ...`,
which will fail immediately — that file doesn't exist. The tree's own
`README.md` says as much implicitly: its "Building" section instructs a human to
open Xcode, create a new macOS App project, delete Xcode's scaffold files, and
add the `.swift` files to the target manually. That one-time manual step has
never been done and committed.

## Implication for Claude Code

Do not expect `swift build`, `xcodebuild`, or any CI step to succeed here without
first creating and committing an `.xcodeproj`. If asked to work on the menu bar
app surface and a real, buildable result is needed, prefer
`../PortCheckerMenuBarPy/` (wired to `make build-pyapp`, actually builds via
py2app) over this Swift stub, unless the user specifically wants Swift.

There is also an older, stale duplicate of this tree at the repo root
(`../PortCheckerMenuBar/`) — do not edit that one; see the root `CLAUDE.md`.

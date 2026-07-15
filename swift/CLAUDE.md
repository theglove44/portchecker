# CLAUDE.md — swift/

Active native app source lives in `swift/PortCheckerMenuBar/`.

## Build system

Root `Package.swift` defines macOS 14+ executable target using Swift 6. No
`.xcodeproj` is required.

```bash
swift build
make build-swiftapp
```

`make build-swiftapp` uses `script/build_and_run.sh`: builds Python CLI, copies
it into app resources, compiles Swift package, creates `dist/Port Checker.app`,
and ad-hoc signs local bundle.

App is buildable but remains development-distributed. No notarization, installer,
App Store packaging, or release automation exists.

## Source tree

- `PortCheckerMenuBarApp.swift` — scenes, menu extra, settings, app activation
- `DashboardView.swift` — main window
- `MenuContentView.swift` — menu bar UI
- `PortScanner.swift` — CLI bridge and app state
- `ServiceDetailView.swift` — service details/actions
- `SettingsView.swift` — settings and favorites
- `Resources/portchecker` — generated bundled CLI; do not hand-edit

Older root `../PortCheckerMenuBar/` tree is stale duplicate. Do not edit it.

# Port Checker Menu Bar (Swift)

A native macOS menu bar app built with SwiftUI.

## Features

- 📊 Native macOS menu bar integration
- 🔢 Badge count showing active services
- 📁 Grouped by project folder
- ⭐ Favorites section
- 🔒 System services protection
- ⚙️ Settings window
- 🔔 Notifications for service changes
- ⌨️ Full keyboard shortcut support

## Requirements

- macOS 14.0+
- Xcode 15.0+
- Swift 5.9+

## Building

### Command Line

```bash
make build-swiftapp
# App: dist/Port Checker.app
```

`Package.swift` is the build target. `script/build_and_run.sh` builds the CLI,
bundles it into a signed local `.app`, and can run or verify the app.

## Architecture

```
PortCheckerMenuBarApp.swift    - App entry point, MenuBarExtra setup
PortScanner.swift              - Business logic, CLI communication
MenuContentView.swift          - Main menu UI
ServiceDetailView.swift        - Service details sheet
SettingsView.swift             - Settings window
```

## Bundling with CLI

To create a standalone app that includes the CLI:

1. Build the CLI first:
   ```bash
   make build-cli
   ```

2. Copy CLI into app bundle:
   ```bash
   cp dist/portchecker "swift/PortCheckerMenuBar/Resources/"
   ```

3. Build the app - it will automatically find the bundled CLI

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| ⌘R | Refresh |
| ⌘, | Settings |
| ⌘Q | Quit |
| ⌘↩ | Stop service (in detail view) |

## Notifications

The app can show notifications when:
- A favorite service starts/stops
- A new service appears
- A service disappears

Enable in Settings.

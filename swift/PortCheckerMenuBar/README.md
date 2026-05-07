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

### Option 1: Xcode (Development)

1. Open this folder in Xcode
2. Select "PortCheckerMenuBar" scheme
3. Build and run (⌘R)

### Option 2: Command Line (Production)

```bash
# Build the app
xcodebuild -project PortCheckerMenuBar.xcodeproj \
    -scheme PortCheckerMenuBar \
    -configuration Release \
    -derivedDataPath build

# The app will be at:
# build/Build/Products/Release/Port Checker.app
```

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

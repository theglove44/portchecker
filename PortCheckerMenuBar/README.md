# Port Checker Menu Bar App

This is a small SwiftUI menu bar app that calls the `portchecker` CLI and shows
which ports are in use. It can also stop services safely (system services are
still blocked).

## Requirements

- macOS 13+ (uses `MenuBarExtra`)
- Xcode 14+
- The `portchecker` CLI built or available in your PATH

## How to build in Xcode

1. Open Xcode and create a new **App** project (macOS).
2. Set the deployment target to macOS 13 or newer.
3. Delete the default SwiftUI files that Xcode created.
4. Add these files to the target:
   - `PortCheckerMenuBarApp.swift`
   - `MenuContentView.swift`
   - `PortScanner.swift`
   - `PortService.swift`
5. Build and run.

## First run

1. Click the menu bar icon.
2. Choose **Set CLI Path...** and select the `portchecker` executable.
   - Example: `dist/portchecker`
3. Click **Refresh** if needed.

## What it does

- Runs `portchecker scan --json` to list services.
- Uses `portchecker stop --pid <PID> --yes` to stop a service.

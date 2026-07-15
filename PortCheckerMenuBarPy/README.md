# Port Checker Menu Bar App (Python)

This builds a macOS menu bar app without Xcode. It uses the `portchecker` CLI
under the hood, so the menu bar always shows what ports are currently in use.

## Requirements

- macOS 12+ recommended
- Python 3.10+
- Xcode Command Line Tools (not the full Xcode app)

## Build the app

From repository root:

```bash
make install-dev
make build-pyapp
```

This produces `dist/Port Checker (Python).app`.

## First run

1. Launch `dist/Port Checker (Python).app`.
2. Click the menu bar icon.
3. Choose **Set CLI Path...** and select your `portchecker` executable.
   - Example: `dist/portchecker`
4. Click **Refresh** if needed.

## Notes

- System services are hidden by default and blocked from stopping.
- You can provide a custom CLI path with the `PORTCHECKER_CLI` environment variable.

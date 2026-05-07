# Port Checker Menu Bar App (Python)

This builds a macOS menu bar app without Xcode. It uses the `portchecker` CLI
under the hood, so the menu bar always shows what ports are currently in use.

## Requirements

- macOS 12+ recommended
- Python 3.9+
- Xcode Command Line Tools (not the full Xcode app)

## Build the app

```bash
cd PortCheckerMenuBarPy
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py py2app
```

This produces `dist/Port Checker.app`.

## First run

1. Launch the app from `PortCheckerMenuBarPy/dist/Port Checker.app`.
2. Click the menu bar icon.
3. Choose **Set CLI Path...** and select your `portchecker` executable.
   - Example: `dist/portchecker`
4. Click **Refresh** if needed.

## Notes

- System services are hidden by default and blocked from stopping.
- You can provide a custom CLI path with the `PORTCHECKER_CLI` environment variable.

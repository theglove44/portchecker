# Port Checker 🔌

A beautiful macOS menu bar app and CLI tool to view and manage running development services on ports. Never forget to stop a dev server again!

## Features

- 📊 **Visual Menu Bar App** - Native macOS SwiftUI interface with rich UI
- 🔍 **Port Scanning** - Instantly see what's running on your ports
- 🛡️ **Security Assessment** - Detect exposed services and risky configurations
- 🔎 **Service Fingerprinting** - Identify what's actually running (MySQL, Redis, etc.)
- ⭐ **Favorites** - Track your commonly used development ports
- 🚫 **Safe Stopping** - Built-in protection against killing system services
- 🔔 **Notifications** - Get notified when services start/stop
- ⌨️ **Keyboard Shortcuts** - Quick actions with native macOS shortcuts

## Screenshots

![Menu Bar App](docs/screenshot-menu.png)
*Main menu with grouped services*

![Service Details](docs/screenshot-detail.png)
*Service details with security info*

![Settings](docs/screenshot-settings.png)
*Settings window*

## Installation

### Option 1: Homebrew (Recommended)

```bash
brew install portchecker
```

### Option 2: Download Release

1. Download the latest release from [Releases](https://github.com/portchecker/portchecker/releases)
2. Drag "Port Checker.app" to your Applications folder
3. Optionally copy the CLI: `cp /Applications/Port\ Checker.app/Contents/Resources/portchecker /usr/local/bin/`

### Option 3: Build from Source

```bash
# Clone the repository
git clone https://github.com/portchecker/portchecker.git
cd portchecker

# Build everything (requires Xcode for Swift app)
make build

# Or build just the CLI
make build-cli

# Or build Python menu bar app (no Xcode required)
make build-pyapp
```

## Usage

### Menu Bar App

Launch "Port Checker" from your Applications folder. The app lives in your menu bar (📊 icon).

**Features:**
- **Badge Count** - Shows number of active services
- **Project Grouping** - Services grouped by folder
- **Favorites** - Pin important services to the top
- **Security Indicators** - Exposed ports highlighted in orange
- **Keyboard Shortcuts:**
  - `⌘R` - Refresh
  - `⌘,` - Settings
  - `⌘Q` - Quit

Click a service to see details and stop it.

### CLI

```bash
# Scan for services
portchecker scan

# Check specific ports
portchecker check 3000 8080 5432

# Security assessment with exposure check
portchecker security

# List exposed ports
portchecker exposed

# Fingerprint services
portchecker fingerprint

# Manage favorites
portchecker fav-add 3000 "Frontend" --note "React dev server"
portchecker fav-status
portchecker fav-stop "Frontend"

# Stop services
portchecker stop 1              # By ID from scan
portchecker stop --pid 1234     # By PID
portchecker stop --force        # Force kill

# JSON output for scripting
portchecker scan --json
portchecker security --json
```

## Project Structure

```
portchecker/
├── src/portchecker/           # Core Python package (modular)
│   ├── models.py              # Data models (PortProcess, etc.)
│   ├── scanner.py             # Port scanning (lsof/psutil)
│   ├── security.py            # Security assessment
│   ├── fingerprint.py         # Service fingerprinting
│   ├── process_control.py     # Start/stop processes
│   ├── config.py              # Settings/favorites management
│   └── cli.py                 # CLI interface (typer)
├── swift/                     # Swift menu bar app
│   └── PortCheckerMenuBar/    # Native SwiftUI app
├── PortCheckerMenuBarPy/      # Python menu bar app (fallback)
├── tests/                     # pytest tests
├── scripts/                   # Build scripts
├── Makefile                   # Build automation
└── pyproject.toml            # Python package config
```

## Development

### Setup

```bash
# Create virtual environment and install dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Run linter
make lint

# Run CLI in dev mode
make run
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ -v --cov=src/portchecker --cov-report=html
```

### Building

```bash
# Build CLI only
make build-cli

# Build Python menu bar app
make build-pyapp

# Build everything (requires Xcode)
make build

# Clean build artifacts
make clean
```

## Architecture

### Core Package (`src/portchecker/`)

The Python package is modularized for maintainability:

- **models.py** - `PortProcess` dataclass and constants (port mappings, fingerprints)
- **scanner.py** - Uses `lsof` for fast port scanning, `psutil` for process enrichment
- **security.py** - Exposure detection, security scoring, risk assessment
- **fingerprint.py** - TCP service fingerprinting with banner grabbing
- **config.py** - JSON-based configuration and favorites storage
- **cli.py** - Rich CLI using Typer with colored output

### Menu Bar Apps

**Swift App (Recommended):**
- Native SwiftUI with `MenuBarExtra`
- Bundles CLI as resource
- Settings window with `AppStorage`
- Notifications with `UNUserNotificationCenter`
- Service grouping and detail popovers

**Python App (Fallback):**
- Uses `rumps` for menu bar integration
- Compatible with macOS 12+
- No Xcode required

## Security Features

- **System Process Protection** - Cannot accidentally stop system services (launchd, sshd, etc.)
- **Exposure Detection** - Warns when dev servers are accessible from the network
- **Risk Port Alerts** - Flags potentially dangerous ports (Telnet, FTP, RDP, etc.)
- **Root User Warnings** - Alerts when services run as root
- **Confirmation Dialogs** - Always confirm before stopping services

## Configuration

Configuration is stored in `~/.config/portchecker/`:

- `config.json` - App settings
- `favorites.json` - Favorite ports

## Requirements

- **macOS 14+** (for Swift menu bar app)
- **macOS 12+** (for Python menu bar app)
- **Python 3.9+** (for CLI)
- **Xcode 15+** (for building Swift app)
- `lsof` command (pre-installed on macOS)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style

```bash
# Format before committing
make format

# Check linting
make lint
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

Made with ❤️ for developers who forget to stop their dev servers.

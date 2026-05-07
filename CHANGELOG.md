# Changelog

All notable changes to Port Checker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-XX-XX

### Added
- Complete modular refactor of Python package
- Native SwiftUI menu bar app with rich UI
- Project grouping in menu bar
- Favorites support with ⭐ section
- Security issue highlighting
- Port exposure detection
- Service detail popovers
- Settings window with `⌘,` shortcut
- Menu bar badge showing active service count
- Auto-refresh with configurable interval
- Notifications for service changes
- Comprehensive test suite with pytest
- Build automation with Makefile
- pyproject.toml for modern Python packaging

### Changed
- Split monolithic `portchecker.py` into modular package
- Improved CLI with better help text and error messages
- Enhanced security assessment with more checks
- Better process identification for interpreted languages

### Security
- Added protection against stopping critical system services
- Exposure detection for network-accessible services
- Risk port alerts (Telnet, FTP, RDP, VNC, etc.)

## [0.9.0] - Previous Version

### Added
- Initial CLI implementation
- Basic port scanning with lsof
- Service fingerprinting
- Security scoring
- Favorites management
- Stop service functionality
- PyInstaller build
- Python rumps menu bar app
- SwiftUI menu bar prototype

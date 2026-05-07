#!/usr/bin/env python3
"""Enhanced Port Checker Menu Bar App using rumps."""

import json
import os
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import rumps
from AppKit import NSModalResponseOK, NSOpenPanel

APP_NAME = "Ports"
APP_VERSION = "1.0.0"

CONFIG_DIR = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    "PortCheckerMenuBar",
)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# Default config
DEFAULT_CONFIG = {
    "cli_path": "",
    "show_system": False,
    "auto_refresh": True,
    "refresh_interval": 30,
    "show_notifications": True,
    "favorites": [],
}


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Merge with defaults
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            return merged
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def find_cli_in_path() -> Optional[str]:
    """Find portchecker in PATH."""
    try:
        result = subprocess.run(
            ["/usr/bin/which", "portchecker"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            return path if path else None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def get_bundled_cli() -> Optional[str]:
    """Get CLI bundled with the app."""
    # Get the app bundle directory (py2app places resources in Contents/Resources)
    bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Try various locations for bundled CLI
    candidates = [
        # Directly in Resources (py2app with DATA_FILES)
        os.path.join(bundle_dir, "Resources", "portchecker"),
        # Nested Resources/Resources (py2app quirk)
        os.path.join(bundle_dir, "Resources", "Resources", "portchecker"),
        # Direct in bundle dir
        os.path.join(bundle_dir, "portchecker"),
        # Relative to build dir
        os.path.join(bundle_dir, "..", "dist", "portchecker"),
        os.path.join(bundle_dir, "..", "..", "dist", "portchecker"),
    ]
    
    for candidate in candidates:
        resolved = os.path.abspath(candidate)
        if os.path.isfile(resolved) and os.access(resolved, os.X_OK):
            return resolved
    
    return None


def resolve_cli_path(config: Dict[str, Any]) -> Optional[str]:
    """Resolve CLI path from various sources."""
    # 1. Configured path
    config_path = config.get("cli_path", "").strip()
    if config_path and os.path.isfile(config_path) and os.access(config_path, os.X_OK):
        return config_path
    
    # 2. Environment variable
    env_path = os.environ.get("PORTCHECKER_CLI", "").strip()
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path
    
    # 3. Bundled CLI
    bundled = get_bundled_cli()
    if bundled:
        return bundled
    
    # 4. PATH
    return find_cli_in_path()


class PortCheckerApp(rumps.App):
    """Main menu bar application."""
    
    def __init__(self) -> None:
        super().__init__(APP_NAME, template=True)
        self.config = load_config()
        self.services: List[Dict[str, Any]] = []
        self.last_error: Optional[str] = "Initializing..."
        self.last_services_state: set = set()
        
        # Setup auto-refresh timer
        self.timer: Optional[rumps.Timer] = None
        self._setup_timer()
        
        # Initial refresh
        self.refresh()
    
    def _setup_timer(self) -> None:
        """Setup auto-refresh timer."""
        if self.timer:
            self.timer.stop()
        
        if self.config.get("auto_refresh", True):
            interval = self.config.get("refresh_interval", 30)
            self.timer = rumps.Timer(self._auto_refresh, interval)
            self.timer.start()
    
    def _auto_refresh(self, sender: rumps.Timer) -> None:
        """Auto-refresh callback."""
        # Run in background thread
        threading.Thread(target=self._refresh_async, daemon=True).start()
    
    def _refresh_async(self) -> None:
        """Async refresh for timer."""
        services, _ = self.scan_services()
        self.services = services
        
        # Check for changes
        if self.config.get("show_notifications", True):
            self._check_changes(services)
        
        # Update menu on main thread
        rumps.Timer(lambda _: self.update_menu(), 0.01).start()
    
    def _check_changes(self, current_services: List[Dict[str, Any]]) -> None:
        """Check for service changes and notify."""
        current_ports = {s.get("port") for s in current_services}
        
        # New services
        new_ports = current_ports - self.last_services_state
        for port in new_ports:
            service = next((s for s in current_services if s.get("port") == port), None)
            if service and not service.get("is_system"):
                self._notify("Service Started", f"{service.get('app', 'Unknown')} on port {port}")
        
        # Stopped services
        stopped_ports = self.last_services_state - current_ports
        for port in stopped_ports:
            self._notify("Service Stopped", f"Port {port} is no longer active")
        
        self.last_services_state = current_ports
    
    def _notify(self, title: str, message: str) -> None:
        """Show notification."""
        try:
            rumps.notification(title, "", message)
        except Exception:
            pass  # Notifications may not be available
    
    def refresh(self, _sender: Optional[rumps.MenuItem] = None) -> None:
        """Manually refresh services."""
        services, error = self.scan_services()
        self.last_error = error
        self.services = services
        self.last_services_state = {s.get("port") for s in services}
        self.update_menu()
    
    def scan_services(self) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Scan for services."""
        cli_path = resolve_cli_path(self.config)
        if not cli_path:
            # Debug: show what paths were tried
            paths_checked = [
                self.config.get("cli_path", ""),
                os.environ.get("PORTCHECKER_CLI", ""),
                get_bundled_cli(),
                find_cli_in_path(),
            ]
            checked_str = ", ".join([p for p in paths_checked if p]) or "none"
            return [], f"CLI not found. Checked: {checked_str[:60]}"
        
        # Debug: verify CLI is executable
        if not os.access(cli_path, os.X_OK):
            return [], f"CLI not executable: {cli_path[-40:]}"
        
        args = [cli_path, "scan", "--json"]
        if self.config.get("show_system", False):
            args.append("--show-system")
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            return [], f"Failed to run: {str(e)[:50]}"
        except Exception as e:
            return [], f"Error: {str(e)[:50]}"
        
        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else ""
            stdout = result.stdout.strip() if result.stdout else ""
            message = stderr or stdout or f"Exit code {result.returncode}"
            return [], f"CLI error: {message[:60]}"
        
        output = result.stdout.strip()
        stderr_output = result.stderr.strip() if result.stderr else ""
        
        # Debug: log raw output
        debug_info = f"Exit:{result.returncode} Out:{len(output)} Err:{len(stderr_output)}"
        if output:
            debug_info += f" First100:{output[:100]}"
        if stderr_output:
            debug_info += f" Err:{stderr_output[:50]}"
        
        if not output:
            return [], f"Empty output. {debug_info}"
        
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            return [], f"JSON error: {str(e)[:30]}. Raw:{output[:50]}"
        
        if not isinstance(data, list):
            return [], f"Expected list, got {type(data).__name__}"
        
        # Sort by port
        data.sort(key=lambda item: item.get("port", 0))
        return data, None
    
    def update_menu(self) -> None:
        """Update the menu with current services."""
        self.menu.clear()
        
        # Update icon badge
        count = len([s for s in self.services if not s.get("is_system")])
        self.title = APP_NAME if count == 0 else f"{APP_NAME} ({count})"
        
        # Show CLI path for debugging
        cli_path = resolve_cli_path(self.config)
        if cli_path:
            cli_display = f"CLI: ...{cli_path[-30:]}" if len(cli_path) > 30 else f"CLI: {cli_path}"
            cli_item = rumps.MenuItem(cli_display)
            cli_item.set_callback(None)
            self.menu.add(cli_item)
            self.menu.add(rumps.separator)
        
        # Error message
        if self.last_error:
            error_item = rumps.MenuItem(f"⚠️ {self.last_error[:50]}")
            error_item.set_callback(None)
            self.menu.add(error_item)
            self.menu.add(rumps.separator)
        
        # Services grouped by project
        if not self.services:
            empty_item = rumps.MenuItem("No ports in use")
            empty_item.set_callback(None)
            self.menu.add(empty_item)
            
            # Debug: show error if any
            if self.last_error:
                debug_item = rumps.MenuItem(f"Debug: {self.last_error[:40]}")
                debug_item.set_callback(None)
                self.menu.add(debug_item)
        else:
            self._add_grouped_services()
        
        self.menu.add(rumps.separator)
        
        # Refresh button
        refresh_item = rumps.MenuItem("🔄 Refresh", callback=self.refresh)
        refresh_item._menuitem.setKeyEquivalentModifierMask_(1 << 20)  # Cmd
        refresh_item._menuitem.setKeyEquivalent_("r")
        self.menu.add(refresh_item)
        
        # Show system toggle
        show_system_item = rumps.MenuItem("Show System Services")
        show_system_item.state = 1 if self.config.get("show_system") else 0
        show_system_item.set_callback(self.toggle_system_services)
        self.menu.add(show_system_item)
        
        # Stop all
        stop_all_item = rumps.MenuItem("⏹ Stop All Listed", callback=self.stop_all)
        non_system = [s for s in self.services if not s.get("is_system")]
        if not non_system:
            stop_all_item.set_callback(None)
        self.menu.add(stop_all_item)
        
        self.menu.add(rumps.separator)
        
        # Settings
        settings_item = rumps.MenuItem("⚙️ Settings...", callback=self.show_settings)
        settings_item._menuitem.setKeyEquivalentModifierMask_(1 << 20)  # Cmd
        settings_item._menuitem.setKeyEquivalent_(",")
        self.menu.add(settings_item)
        
        # About
        about_item = rumps.MenuItem(f"ℹ️ About Port Checker {APP_VERSION}", callback=self.show_about)
        self.menu.add(about_item)
        
        # Quit
        quit_item = rumps.MenuItem("Quit", callback=rumps.quit_application)
        quit_item._menuitem.setKeyEquivalentModifierMask_(1 << 20)  # Cmd
        quit_item._menuitem.setKeyEquivalent_("q")
        self.menu.add(quit_item)
    
    def _add_grouped_services(self) -> None:
        """Add services grouped by project."""
        # Group by project
        favorites = self.config.get("favorites", [])
        favorite_ports = {f["port"] for f in favorites}
        
        grouped: Dict[str, List[Dict]] = {}
        favorite_services = []
        system_services = []
        
        for svc in self.services:
            if svc.get("port") in favorite_ports:
                favorite_services.append(svc)
            elif svc.get("is_system"):
                system_services.append(svc)
            else:
                project = svc.get("project", "Other")
                grouped.setdefault(project, []).append(svc)
        
        # Add favorites section
        if favorite_services:
            fav_header = rumps.MenuItem("⭐ FAVORITES")
            fav_header.set_callback(None)
            self.menu.add(fav_header)
            for svc in favorite_services:
                self._add_service_item(svc)
            self.menu.add(rumps.separator)
        
        # Add projects
        for project in sorted(grouped.keys(), key=lambda x: (x == "Other", x.lower())):
            services = grouped[project]
            
            # Project header
            header = rumps.MenuItem(f"📁 {project}")
            header.set_callback(None)
            self.menu.add(header)
            
            for svc in services:
                self._add_service_item(svc, indent=True)
        
        # Add system services
        if system_services and self.config.get("show_system"):
            self.menu.add(rumps.separator)
            sys_header = rumps.MenuItem("🔒 SYSTEM SERVICES")
            sys_header.set_callback(None)
            self.menu.add(sys_header)
            for svc in system_services:
                self._add_service_item(svc, is_system=True)
    
    def _add_service_item(self, service: Dict[str, Any], indent: bool = False, is_system: bool = False) -> None:
        """Add a single service menu item."""
        port = service.get("port", "?")
        app = service.get("app", "Unknown")
        project = service.get("project", "")
        
        prefix = "    " if indent else ""
        exposed = "🌐" if service.get("is_exposed") else ""
        icon = "🔒" if is_system else (exposed or "●")
        
        title = f"{prefix}{icon} {port}: {app}"
        if project and project not in ["Unknown", "Other"] and not indent:
            title += f" ({project})"
        
        if is_system:
            item = rumps.MenuItem(title)
            item.set_callback(None)
        else:
            def on_click(_sender, svc=service):
                self.stop_service(svc)
            item = rumps.MenuItem(title, callback=on_click)
        
        self.menu.add(item)
    
    def toggle_system_services(self, _sender: rumps.MenuItem) -> None:
        """Toggle showing system services."""
        self.config["show_system"] = not self.config.get("show_system", False)
        save_config(self.config)
        self.refresh()
    
    def stop_service(self, service: Dict[str, Any]) -> None:
        """Stop a single service."""
        if service.get("is_system"):
            rumps.alert("Cannot Stop", "System services cannot be stopped.")
            return
        
        app = service.get("app", "Unknown")
        port = service.get("port", "?")
        project = service.get("project", "")
        pid = service.get("pid")
        
        message = f"Port {port}"
        if project and project != "Unknown":
            message += f"\nProject: {project}"
        message += f"\nPID: {pid}"
        
        confirm = rumps.alert(
            f"Stop {app}?",
            message,
            ok="Stop",
            cancel="Cancel",
        )
        
        if confirm == 1:
            self.run_stop(pid)
    
    def stop_all(self, _sender: rumps.MenuItem) -> None:
        """Stop all non-system services."""
        targets = [s for s in self.services if not s.get("is_system")]
        if not targets:
            return
        
        confirm = rumps.alert(
            f"Stop {len(targets)} services?",
            "This will stop all listed non-system services.",
            ok="Stop All",
            cancel="Cancel",
        )
        
        if confirm != 1:
            return
        
        for svc in targets:
            self.run_stop(svc.get("pid"))
        
        # Refresh after a short delay
        threading.Timer(1.0, self.refresh).start()
    
    def run_stop(self, pid: Any) -> None:
        """Run stop command."""
        if pid is None:
            return
        
        cli_path = resolve_cli_path(self.config)
        if not cli_path:
            rumps.alert("Error", "CLI not found.")
            return
        
        args = [cli_path, "stop", "--pid", str(pid), "--yes"]
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                error = result.stderr.strip() or "Unknown error"
                rumps.alert("Stop Failed", error)
        except (OSError, subprocess.TimeoutExpired) as e:
            rumps.alert("Error", f"Failed to stop: {e}")
        
        # Refresh after stopping
        self.refresh()
    
    def show_settings(self, _sender: rumps.MenuItem) -> None:
        """Show settings window."""
        # CLI Path
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setMessage_("Select the portchecker CLI executable")
        
        if panel.runModal() == NSModalResponseOK:
            url = panel.URL()
            if url:
                selected = str(url.path())
                if os.path.isfile(selected) and os.access(selected, os.X_OK):
                    self.config["cli_path"] = selected
                    save_config(self.config)
                    self.refresh()
                else:
                    rumps.alert("Invalid", "Please choose an executable file.")
    
    def show_about(self, _sender: rumps.MenuItem) -> None:
        """Show about dialog."""
        rumps.alert(
            "Port Checker",
            f"Version {APP_VERSION}\n\nA menu bar app for managing development services."
        )


if __name__ == "__main__":
    PortCheckerApp().run()

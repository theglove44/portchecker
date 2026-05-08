#!/usr/bin/env python3
"""Port Checker — macOS menu bar app."""

import json
import queue
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import rumps

# When running from the project venv in dev mode, pull in the src package.
_src = Path(__file__).parent.parent / "src"
if _src.exists():
    sys.path.insert(0, str(_src))

from portchecker.config import load_favorites
from portchecker.models import PORT_SERVICES, PortProcess
from portchecker.process_control import can_stop_process, stop_process
from portchecker.scanner import enrich_processes, scan_ports

VERSION = "1.0.0"
PREFS_FILE = (
    Path.home() / "Library" / "Application Support" / "PortChecker" / "prefs.json"
)
REFRESH_OPTIONS = [10, 30, 60, 300]
REFRESH_LABELS = {10: "10 sec", 30: "30 sec", 60: "1 min", 300: "5 min"}
HTTP_SERVICES = {"HTTP", "HTTP-Alt", "HTTPS", "HTTPS-Alt"}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _svc_name(port: int) -> str:
    return PORT_SERVICES[port][0] if port in PORT_SERVICES else ""


def _is_http(port: int) -> bool:
    return _svc_name(port) in HTTP_SERVICES


def _service_line(proc: PortProcess) -> str:
    """Single readable line: :port  App Name  [SVC]"""
    app = proc.app or proc.command
    svc = _svc_name(proc.port)
    tag = f"  [{svc}]" if svc and svc.lower() not in app.lower() else ""
    return f":{proc.port}  {app}{tag}"


def _copy(text: str) -> None:
    subprocess.run(["pbcopy"], input=text.encode(), check=True)


def _inert(title: str) -> rumps.MenuItem:
    """Non-clickable info item."""
    item = rumps.MenuItem(title)
    item.set_callback(None)
    return item


def _divider() -> rumps.MenuItem:
    """Visual divider for use inside submenus."""
    return _inert("─" * 18)


# ── App ───────────────────────────────────────────────────────────────────────


class PortCheckerApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("Ports", template=True)

        # Preferences (persisted)
        self._auto_refresh: bool = True
        self._refresh_interval: int = 30
        self._show_system: bool = False
        self._notifications: bool = True
        self._load_prefs()

        # Runtime state
        self._procs: list[PortProcess] = []
        self._scanning: bool = False
        self._last_updated: str = ""
        self._prev_ports: set[int] = set()
        self._first_scan: bool = True  # suppress startup notifications

        # Producer/consumer: background thread → queue → main-thread drain timer.
        # This is the only safe way to trigger a UI rebuild from a background thread
        # in rumps — NSTimer scheduled from a non-main thread won't fire.
        self._results: queue.Queue[list[PortProcess]] = queue.Queue()
        self._poll = rumps.Timer(self._drain, 0.1)
        self._poll.start()

        # Auto-refresh timer (fires on main thread, kicks off background scan)
        self._timer: rumps.Timer | None = None
        self._start_timer()

        # Initial scan
        threading.Thread(target=self._scan, daemon=True).start()

    # ── Preferences ───────────────────────────────────────────────────────

    def _load_prefs(self) -> None:
        try:
            with open(PREFS_FILE) as f:
                p = json.load(f)
            self._auto_refresh = bool(p.get("auto_refresh", True))
            self._refresh_interval = int(p.get("refresh_interval", 30))
            self._show_system = bool(p.get("show_system", False))
            self._notifications = bool(p.get("notifications", True))
        except Exception:
            pass

    def _save_prefs(self) -> None:
        PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PREFS_FILE, "w") as f:
            json.dump(
                {
                    "auto_refresh": self._auto_refresh,
                    "refresh_interval": self._refresh_interval,
                    "show_system": self._show_system,
                    "notifications": self._notifications,
                },
                f,
                indent=2,
            )

    # ── Timers ────────────────────────────────────────────────────────────

    def _start_timer(self) -> None:
        if self._timer:
            self._timer.stop()
        if self._auto_refresh:
            self._timer = rumps.Timer(self._on_timer, self._refresh_interval)
            self._timer.start()

    def _on_timer(self, _: Any) -> None:
        """Auto-refresh: kick off a background scan."""
        if not self._scanning:
            threading.Thread(target=self._scan, daemon=True).start()

    # ── Scanning ──────────────────────────────────────────────────────────

    def _scan(self) -> None:
        """Run in a background thread. Posts result to queue for main thread."""
        self._scanning = True
        try:
            procs = enrich_processes(scan_ports(), self._show_system)
        except Exception:
            procs = []
        self._scanning = False
        self._results.put(procs)

    def _drain(self, _: Any) -> None:
        """Main-thread poll timer. Picks up completed scans and rebuilds menu."""
        try:
            procs = self._results.get_nowait()
        except queue.Empty:
            return

        self._procs = procs
        self._last_updated = datetime.now().strftime("%-I:%M %p")

        if self._first_scan:
            # On startup, just snapshot — don't fire a notification for every
            # already-running service.
            self._prev_ports = {p.port for p in procs if not p.is_system}
            self._first_scan = False
        elif self._notifications:
            try:
                self._notify_changes(procs)
            except Exception:
                pass

        self._rebuild()

    def _notify_changes(self, procs: list[PortProcess]) -> None:
        cur = {p.port for p in procs if not p.is_system}
        for port in cur - self._prev_ports:
            proc = next((p for p in procs if p.port == port), None)
            if proc:
                name = proc.app or proc.command
                rumps.notification("Port Checker", "Started", f"{name}  :{port}")
        for port in self._prev_ports - cur:
            rumps.notification("Port Checker", "Stopped", f":{port} closed")
        self._prev_ports = cur

    # ── Menu ──────────────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        try:
            self._rebuild_menu()
        except Exception as e:
            self.menu.clear()
            self.menu.add(_inert(f"⚠️  Error: {e}"))
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    def _rebuild_menu(self) -> None:
        dev = [p for p in self._procs if not p.is_system]
        sys_procs = [p for p in self._procs if p.is_system]

        count = len(dev)
        self.title = f"Ports  {count}" if count else "Ports"

        self.menu.clear()

        fav_ports = {f["port"] for f in load_favorites()}
        favs = [p for p in dev if p.port in fav_ports]
        rest = [p for p in dev if p.port not in fav_ports]

        # ── Favorites ──
        if favs:
            self.menu.add(_inert("⭐  Favorites"))
            for proc in favs:
                self.menu.add(self._service_item(proc))
            self.menu.add(rumps.separator)

        # ── Dev services grouped by project ──
        if rest:
            groups: dict[str, list[PortProcess]] = {}
            for proc in rest:
                groups.setdefault(proc.project or "Other", []).append(proc)

            first = True
            for project in sorted(
                groups, key=lambda x: (x in ("Unknown", "Other"), x.lower())
            ):
                if not first:
                    self.menu.add(rumps.separator)
                first = False
                self.menu.add(_inert(f"📁  {project}"))
                for proc in groups[project]:
                    self.menu.add(self._service_item(proc, indent=True))

        if not dev:
            self.menu.add(_inert("No services running"))

        # ── System services (when shown) ──
        if sys_procs and self._show_system:
            self.menu.add(rumps.separator)
            self.menu.add(_inert("🔒  System"))
            for proc in sys_procs:
                self.menu.add(_inert(f"    :{proc.port}  {proc.command}"))

        self.menu.add(rumps.separator)

        # ── Timestamp + Refresh ──
        if self._last_updated:
            self.menu.add(_inert(f"Updated {self._last_updated}"))

        refresh = rumps.MenuItem("Refresh", callback=self._on_refresh)
        refresh._menuitem.setKeyEquivalentModifierMask_(1 << 20)
        refresh._menuitem.setKeyEquivalent_("r")
        self.menu.add(refresh)

        self.menu.add(rumps.separator)

        # ── Auto-refresh submenu ──
        if self._auto_refresh:
            auto_label = f"Auto-refresh  ({REFRESH_LABELS[self._refresh_interval]})"
        else:
            auto_label = "Auto-refresh  (off)"
        auto = rumps.MenuItem(auto_label)
        auto.state = 1 if self._auto_refresh else 0

        toggle = rumps.MenuItem(
            "Enabled" if self._auto_refresh else "Disabled",
            callback=self._toggle_auto_refresh,
        )
        toggle.state = 1 if self._auto_refresh else 0
        auto.add(toggle)
        auto.add(_divider())

        for secs in REFRESH_OPTIONS:
            opt = rumps.MenuItem(
                REFRESH_LABELS[secs],
                callback=self._make_interval_setter(secs),
            )
            opt.state = 1 if (self._auto_refresh and secs == self._refresh_interval) else 0
            auto.add(opt)

        self.menu.add(auto)

        show_sys = rumps.MenuItem(
            "Show system services", callback=self._toggle_show_system
        )
        show_sys.state = 1 if self._show_system else 0
        self.menu.add(show_sys)

        notifs = rumps.MenuItem("Notifications", callback=self._toggle_notifications)
        notifs.state = 1 if self._notifications else 0
        self.menu.add(notifs)

        self.menu.add(rumps.separator)

        quit_item = rumps.MenuItem("Quit", callback=rumps.quit_application)
        quit_item._menuitem.setKeyEquivalentModifierMask_(1 << 20)
        quit_item._menuitem.setKeyEquivalent_("q")
        self.menu.add(quit_item)

    # ── Service submenu ───────────────────────────────────────────────────

    def _service_item(self, proc: PortProcess, indent: bool = False) -> rumps.MenuItem:
        pad = "    " if indent else ""
        exposed = "  🌐" if proc.is_exposed else ""
        parent = rumps.MenuItem(f"{pad}{_service_line(proc)}{exposed}")

        app = proc.app or proc.command
        port = proc.port

        parent.add(_inert(f"Port:    {port}"))
        parent.add(_inert(f"App:     {app}"))
        parent.add(_inert(f"PID:     {proc.pid}"))
        parent.add(_inert(f"User:    {proc.user}"))
        if proc.project and proc.project not in ("Unknown", "Other", "Ended", "Unavailable"):
            parent.add(_inert(f"Project: {proc.project}"))

        parent.add(_divider())

        parent.add(rumps.MenuItem(
            f"Copy  :{port}",
            callback=lambda _, p=port: _copy(str(p)),
        ))
        parent.add(rumps.MenuItem(
            f"Copy  localhost:{port}",
            callback=lambda _, p=port: _copy(f"localhost:{p}"),
        ))
        if _is_http(port):
            parent.add(rumps.MenuItem(
                "Open in browser",
                callback=lambda _, p=port: subprocess.run(["open", f"http://localhost:{p}"]),
            ))

        parent.add(_divider())

        parent.add(rumps.MenuItem(
            "Stop service…",
            callback=lambda _, p=proc: self._stop(p),
        ))

        return parent

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _stop(self, proc: PortProcess) -> None:
        ok, reason = can_stop_process(proc)
        if not ok:
            rumps.alert("Cannot stop", reason)
            return
        app = proc.app or proc.command
        if rumps.alert(
            f"Stop {app}?",
            f"Port {proc.port}  ·  PID {proc.pid}",
            ok="Stop",
            cancel="Cancel",
        ) == 1:
            success, msg = stop_process(proc.pid)
            if success:
                threading.Thread(target=self._scan, daemon=True).start()
            else:
                rumps.alert("Failed to stop", msg)

    def _on_refresh(self, _: Any) -> None:
        if not self._scanning:
            threading.Thread(target=self._scan, daemon=True).start()

    def _toggle_auto_refresh(self, _: Any) -> None:
        self._auto_refresh = not self._auto_refresh
        self._save_prefs()
        self._start_timer()
        self._rebuild()

    def _make_interval_setter(self, secs: int):
        def callback(_: Any) -> None:
            self._refresh_interval = secs
            self._auto_refresh = True
            self._save_prefs()
            self._start_timer()
            self._rebuild()
        return callback

    def _toggle_show_system(self, _: Any) -> None:
        self._show_system = not self._show_system
        self._save_prefs()
        threading.Thread(target=self._scan, daemon=True).start()

    def _toggle_notifications(self, _: Any) -> None:
        self._notifications = not self._notifications
        self._save_prefs()
        self._rebuild()


if __name__ == "__main__":
    PortCheckerApp().run()

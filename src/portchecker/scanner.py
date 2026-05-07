"""Port scanning functionality."""

import os
import re
import subprocess
from typing import List, Set

import psutil

from .models import SYSTEM_PROCESSES, SYSTEM_USERS, PortProcess


def is_system_process(command: str, user: str) -> bool:
    """Check if a process is a system process."""
    cmd_lower = command.lower()
    return (
        cmd_lower in SYSTEM_PROCESSES
        or user in SYSTEM_USERS
        or user.startswith('_')
    )


def friendly_app_name(command: str, cmdline: List[str]) -> str:
    """Generate a friendly app name from command and arguments."""
    if not cmdline:
        return command

    exe_name = os.path.basename(cmdline[0]).lower()

    # Handle Java with -jar
    if exe_name == 'java' and '-jar' in cmdline:
        idx = cmdline.index('-jar')
        if idx + 1 < len(cmdline):
            return f"{command} ({os.path.basename(cmdline[idx + 1])})"

    # Handle interpreted languages (python, node, ruby)
    if exe_name.startswith('python') or exe_name in {'node', 'ruby'}:
        for arg in cmdline[1:]:
            if arg.startswith('-'):
                continue
            return f"{command} ({os.path.basename(arg)})"

    return command


def scan_ports() -> List[PortProcess]:
    """Scan for processes listening on TCP ports.

    Uses lsof for fast scanning of listening ports.

    Returns:
        List of PortProcess objects
    """
    try:
        result = subprocess.run(
            ['lsof', '-iTCP', '-sTCP:LISTEN', '-P', '-n'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return []

        processes = []
        seen: Set[tuple] = set()

        # Skip header line and parse output
        for line in result.stdout.strip().split('\n')[1:]:
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 9:
                cmd = parts[0]
                pid = int(parts[1])
                user = parts[2]
                name = ' '.join(parts[8:])

                # Extract port from address (e.g., "*:8080" or "127.0.0.1:3000 (LISTEN)")
                port_match = re.search(r':(\d+)', name)
                if port_match:
                    port = int(port_match.group(1))
                    key = (pid, port)

                    if key not in seen:
                        seen.add(key)
                        processes.append(PortProcess(
                            command=cmd,
                            pid=pid,
                            user=user,
                            port=port,
                            address=name,
                            is_system=is_system_process(cmd, user)
                        ))

        return processes

    except (subprocess.TimeoutExpired, OSError, ValueError):
        return []


def enrich_processes(processes: List[PortProcess], show_system: bool) -> List[PortProcess]:
    """Enrich process info with app names and project directories.

    Args:
        processes: List of PortProcess objects
        show_system: Whether to include system processes

    Returns:
        Filtered and enriched list of PortProcess objects
    """
    visible = []

    for proc in processes:
        # Filter system processes if not showing them
        if proc.is_system and not show_system:
            continue

        try:
            psutil_proc = psutil.Process(proc.pid)

            # Get friendly app name
            proc.app = friendly_app_name(proc.command, psutil_proc.cmdline())

            # Get username
            proc.user = psutil_proc.username() or proc.user

            # Get project directory
            try:
                cwd = psutil_proc.cwd()
                if cwd and cwd != '/':
                    proc.project = os.path.basename(cwd)
                else:
                    proc.project = 'Unknown'
            except (psutil.AccessDenied, OSError):
                proc.project = 'Unknown'

        except psutil.NoSuchProcess:
            proc.app = proc.command
            proc.project = 'Ended'
        except (psutil.AccessDenied, OSError):
            proc.app = proc.command
            proc.project = 'Unavailable'

        visible.append(proc)

    return visible


def get_process_by_pid(pid: int) -> PortProcess | None:
    """Get a single process by PID."""
    try:
        proc = psutil.Process(pid)
        connections = proc.connections(kind='inet')

        for conn in connections:
            if conn.status == 'LISTEN' and conn.laddr:
                return PortProcess(
                    command=proc.name(),
                    pid=pid,
                    user=proc.username() or 'unknown',
                    port=conn.laddr.port,
                    address=f"{conn.laddr.ip}:{conn.laddr.port}",
                    is_system=is_system_process(proc.name(), proc.username() or '')
                )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    return None

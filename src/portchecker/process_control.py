"""Process control (start/stop) functionality."""

from typing import List, Tuple

import psutil

from .models import PortProcess


def stop_process(pid: int, force: bool = False, timeout: int = 5) -> Tuple[bool, str]:
    """Stop a process by PID.

    Args:
        pid: Process ID to stop
        force: Whether to kill immediately without graceful termination
        timeout: Seconds to wait for graceful termination

    Returns:
        Tuple of (success, message)
    """
    try:
        proc = psutil.Process(pid)

        if force:
            proc.kill()
            return True, f"Killed process {pid}"

        # Try graceful termination first
        proc.terminate()

        try:
            proc.wait(timeout=timeout)
            return True, f"Stopped process {pid}"
        except psutil.TimeoutExpired:
            # Force kill if graceful termination times out
            proc.kill()
            return True, f"Force killed process {pid} after timeout"

    except psutil.NoSuchProcess:
        return False, f"Process {pid} not found"
    except psutil.AccessDenied:
        return False, f"Access denied to stop process {pid}"
    except Exception as e:
        return False, f"Error stopping process {pid}: {e}"


def stop_services(
    services: List[PortProcess], force: bool = False
) -> List[Tuple[PortProcess, bool, str]]:
    """Stop multiple services.

    Args:
        services: List of PortProcess objects to stop
        force: Whether to force kill

    Returns:
        List of (service, success, message) tuples
    """
    results = []
    for svc in services:
        if svc.is_system:
            results.append((svc, False, "Cannot stop system service"))
            continue

        success, message = stop_process(svc.pid, force=force)
        results.append((svc, success, message))

    return results


def can_stop_process(proc: PortProcess) -> Tuple[bool, str]:
    """Check if a process can be stopped.

    Args:
        proc: PortProcess to check

    Returns:
        Tuple of (can_stop, reason)
    """
    if proc.is_system:
        return False, "Cannot stop system service"

    try:
        psutil.Process(proc.pid)
        return True, ""
    except psutil.NoSuchProcess:
        return False, "Process no longer exists"
    except psutil.AccessDenied:
        return False, "Access denied"

"""Security assessment functionality."""

import re
import socket
from typing import List, Tuple

import psutil

from .models import DEV_PORTS, RISKY_PORT_NAMES, RISKY_PORTS, PortProcess


def get_local_ips() -> List[str]:
    """Get list of local non-loopback IP addresses."""
    ips = []
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            if iface.startswith('lo'):
                continue
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                    ips.append(addr.address)
    except (OSError, AttributeError):
        pass
    return ips


def check_port_accessible(ip: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a port is accessible on a specific IP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except (socket.error, OSError):
        return False


def check_exposure(proc: PortProcess) -> Tuple[bool, str]:
    """Check if a port is exposed beyond localhost.

    Args:
        proc: PortProcess to check

    Returns:
        Tuple of (is_exposed, reason)
    """
    addr = proc.address
    port = proc.port

    # Check for all-interface bindings
    if addr.startswith('*:') or addr.startswith('[::]:') or addr.startswith('0.0.0.0:'):
        return True, "Bound to all interfaces"

    # Check for specific non-localhost IP binding
    match = re.search(r'^(\d+\.\d+\.\d+\.\d+):', addr)
    if match:
        ip = match.group(1)
        if not ip.startswith('127.') and check_port_accessible(ip, port):
            return True, f"Accessible via {ip}"

    # Check all local IPs
    for ip in get_local_ips():
        if check_port_accessible(ip, port, timeout=0.5):
            return True, f"Accessible via {ip}"

    return False, "Local only"


def assess_security(proc: PortProcess) -> List[Tuple[str, str, str]]:
    """Assess security issues for a process.

    Args:
        proc: PortProcess to assess

    Returns:
        List of (severity, issue, recommendation) tuples
    """
    issues = []
    port = proc.port
    addr = proc.address

    # HIGH: Exposed non-system service
    if proc.is_exposed and not proc.is_system:
        issues.append((
            'HIGH',
            f"Port {port} exposed",
            f"Bound to {proc.exposure_reason}"
        ))

    # MEDIUM: Risky port
    if port in RISKY_PORTS:
        issues.append((
            'MEDIUM',
            f"Risky port {port}",
            RISKY_PORT_NAMES.get(port, "Known risk")
        ))

    # MEDIUM: Running as root
    if proc.user == 'root' and not proc.is_system:
        issues.append((
            'MEDIUM',
            "Running as root",
            "Use non-root user"
        ))

    # MEDIUM: Bound to all interfaces
    if (addr.startswith('*:') or addr.startswith('[::]:')) and not proc.is_system:
        issues.append((
            'MEDIUM',
            "Bound to all interfaces",
            "Restrict to 127.0.0.1"
        ))

    # LOW: Dev port exposed
    if port in DEV_PORTS and proc.is_exposed and not proc.is_system:
        issues.append((
            'LOW',
            f"Dev port {port} exposed",
            "Dev servers should be local"
        ))

    return issues


def security_score(processes: List[PortProcess]) -> Tuple[int, List[Tuple[str, str, str]]]:
    """Calculate overall security score.

    Args:
        processes: List of PortProcess objects

    Returns:
        Tuple of (score_0-100, all_issues)
    """
    if not processes:
        return 100, []

    all_issues = []
    score = 100

    # Assess each non-system process
    for proc in processes:
        if proc.is_system:
            continue

        issues = assess_security(proc)
        proc.security_issues = issues
        all_issues.extend(issues)

    # Calculate score
    for sev, issue, _ in all_issues:
        if sev == 'HIGH':
            score -= 15
        elif sev == 'MEDIUM':
            score -= 8
        else:
            score -= 3

    # Bonus: no exposed ports
    exposed_count = sum(1 for p in processes if p.is_exposed and not p.is_system)
    if exposed_count == 0 and all_issues:
        score += 5

    return max(0, min(100, score)), all_issues


def score_color(score: int) -> str:
    """Get color name for a security score."""
    if score >= 90:
        return "green"
    elif score >= 70:
        return "yellow"
    elif score >= 50:
        return "orange"
    return "red"


def score_emoji(score: int) -> str:
    """Get emoji for a security score."""
    if score >= 90:
        return "🛡️"
    elif score >= 70:
        return "✅"
    elif score >= 50:
        return "⚠️"
    return "🚨"

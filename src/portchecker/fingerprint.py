"""Service fingerprinting functionality."""

import re
import socket
import ssl
import threading
from typing import Dict, List, Tuple

from .models import FINGERPRINTS, PORT_SERVICES, PortProcess


def fingerprint_port(port: int, timeout: float = 2.0) -> Tuple[str, str, str, str]:
    """Fingerprint a service on a specific port.

    Args:
        port: Port number to check
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (service_name, protocol, version, banner)
    """
    # Check known port mappings first
    if port in PORT_SERVICES:
        svc, proto = PORT_SERVICES[port]
        return svc, proto, "detected", ""

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(('127.0.0.1', port))

        # Try to read banner
        banner = ""
        try:
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
        except socket.timeout:
            pass

        # Handle HTTPS specially
        if port in [443, 8443]:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ss = ctx.wrap_socket(sock, server_hostname='localhost')
                ss.send(b'GET / HTTP/1.0\r\nHost: localhost\r\n\r\n')
                response = ss.recv(4096).decode('utf-8', errors='ignore')
                banner = response.split('\r\n\r\n')[0][:200]
            except ssl.SSLError:
                pass

        sock.close()

        if not banner:
            return "Unknown", "TCP", "no response", ""

        # Try to match fingerprints
        for pattern, service, proto in FINGERPRINTS:
            if re.match(pattern, banner, re.IGNORECASE):
                # Try to extract version
                version_match = re.search(r'[\d]+\.[\d]+\.[\d]+', banner)
                if version_match:
                    version = version_match.group(0)
                elif len(banner) > 10:
                    version = banner[:30] + "..." if len(banner) > 30 else banner
                else:
                    version = "detected"

                return service, proto, version, banner[:100]

        # No fingerprint matched
        return (
            "Unknown",
            "TCP",
            "unidentified",
            banner[:50] + "..." if len(banner) > 50 else banner
        )

    except socket.timeout:
        return "Unknown", "TCP", "timeout", ""
    except ConnectionRefusedError:
        return "Unknown", "TCP", "closed", ""
    except Exception as e:
        return "Unknown", "TCP", f"error: {str(e)[:20]}", ""


def fingerprint_ports(ports: List[int], timeout: float = 2.0) -> Dict[int, Dict]:
    """Fingerprint multiple ports in parallel.

    Args:
        ports: List of port numbers
        timeout: Connection timeout per port

    Returns:
        Dictionary mapping port numbers to fingerprint info
    """
    results: Dict[int, Dict] = {}
    lock = threading.Lock()

    def check(port: int) -> None:
        svc, proto, ver, banner = fingerprint_port(port, timeout)
        with lock:
            results[port] = {
                'service': svc,
                'protocol': proto,
                'version': ver,
                'banner': banner
            }

    threads = [threading.Thread(target=check, args=(p,)) for p in ports]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout * 2)

    return results


def enrich_with_fingerprints(processes: List[PortProcess]) -> None:
    """Enrich processes with fingerprint info in place."""
    if not processes:
        return

    ports = [p.port for p in processes]
    fps = fingerprint_ports(ports)

    for proc in processes:
        if proc.port in fps:
            proc.fingerprint = fps[proc.port]

"""Tests for models module."""

import pytest

from portchecker.models import (
    PortProcess,
    SYSTEM_PROCESSES,
    SYSTEM_USERS,
    PORT_SERVICES,
    RISKY_PORTS,
)


def test_port_process_creation():
    """Test creating a PortProcess."""
    proc = PortProcess(
        command="python",
        pid=1234,
        user="testuser",
        port=8080,
        address="127.0.0.1:8080",
    )
    
    assert proc.command == "python"
    assert proc.pid == 1234
    assert proc.user == "testuser"
    assert proc.port == 8080
    assert proc.address == "127.0.0.1:8080"
    assert proc.is_system is False
    assert proc.app == ""
    assert proc.project == "Unknown"


def test_port_process_to_dict():
    """Test converting PortProcess to dict."""
    proc = PortProcess(
        command="node",
        pid=5678,
        user="dev",
        port=3000,
        address="*:3000",
        is_system=False,
        app="node (app.js)",
        project="myapp",
    )
    
    d = proc.to_dict()
    
    assert d["command"] == "node"
    assert d["pid"] == 5678
    assert d["port"] == 3000
    assert d["is_system"] is False
    assert d["app"] == "node (app.js)"
    assert d["project"] == "myapp"


def test_system_processes_set():
    """Test system processes set contains expected values."""
    assert "launchd" in SYSTEM_PROCESSES
    assert "sshd" in SYSTEM_PROCESSES
    assert "nginx" in SYSTEM_PROCESSES


def test_system_users_set():
    """Test system users set contains expected values."""
    assert "root" in SYSTEM_USERS
    assert "daemon" in SYSTEM_USERS


def test_port_services_mappings():
    """Test common port service mappings."""
    assert PORT_SERVICES[80] == ("HTTP", "Web Server")
    assert PORT_SERVICES[443] == ("HTTPS", "Secure Web")
    assert PORT_SERVICES[22] == ("SSH", "Secure Shell")
    assert PORT_SERVICES[3306] == ("MySQL", "Database")
    assert PORT_SERVICES[5432] == ("PostgreSQL", "Database")
    assert PORT_SERVICES[6379] == ("Redis", "Cache")


def test_risky_ports_set():
    """Test risky ports set."""
    assert 21 in RISKY_PORTS   # FTP
    assert 23 in RISKY_PORTS   # Telnet
    assert 445 in RISKY_PORTS  # SMB
    assert 3389 in RISKY_PORTS # RDP
    assert 5900 in RISKY_PORTS # VNC

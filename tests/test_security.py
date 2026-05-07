"""Tests for security module."""

from unittest.mock import patch

import pytest

from portchecker.models import PortProcess
from portchecker.security import (
    check_port_accessible,
    check_exposure,
    assess_security,
    security_score,
    score_color,
    score_emoji,
)


def test_score_color():
    """Test score color mapping."""
    assert score_color(95) == "green"
    assert score_color(90) == "green"
    assert score_color(80) == "yellow"
    assert score_color(70) == "yellow"
    assert score_color(60) == "orange"
    assert score_color(50) == "orange"
    assert score_color(40) == "red"
    assert score_color(0) == "red"


def test_score_emoji():
    """Test score emoji mapping."""
    assert score_emoji(95) == "🛡️"
    assert score_emoji(90) == "🛡️"
    assert score_emoji(80) == "✅"
    assert score_emoji(70) == "✅"
    assert score_emoji(60) == "⚠️"
    assert score_emoji(50) == "⚠️"
    assert score_emoji(40) == "🚨"
    assert score_emoji(0) == "🚨"


def test_security_score_empty():
    """Test security score with no processes."""
    score, issues = security_score([])
    assert score == 100
    assert issues == []


def test_security_score_perfect():
    """Test security score with safe local-only service."""
    proc = PortProcess(
        command="node",
        pid=1234,
        user="dev",
        port=3000,
        address="127.0.0.1:3000",
        is_system=False,
        is_exposed=False,
    )
    
    score, issues = security_score([proc])
    assert score == 100
    assert issues == []


def test_assess_security_exposed_dev_port():
    """Test security assessment for exposed dev port."""
    proc = PortProcess(
        command="node",
        pid=1234,
        user="dev",
        port=3000,  # Dev port
        address="0.0.0.0:3000",
        is_system=False,
        is_exposed=True,
        exposure_reason="Bound to all interfaces",
    )
    
    issues = assess_security(proc)
    
    # Should have HIGH for exposure, MEDIUM for all interfaces, LOW for dev port
    severities = [i[0] for i in issues]
    assert "HIGH" in severities


def test_assess_security_risky_port():
    """Test security assessment for risky port."""
    proc = PortProcess(
        command="telnetd",
        pid=1234,
        user="root",
        port=23,  # Telnet
        address="127.0.0.1:23",
        is_system=False,
        is_exposed=False,
    )
    
    issues = assess_security(proc)
    
    # Should have MEDIUM for risky port and MEDIUM for root user
    issues_list = [(i[0], i[1]) for i in issues]
    assert any("Risky port" in issue for _, issue in issues_list)


def test_assess_security_root_user():
    """Test security assessment for root user."""
    proc = PortProcess(
        command="myapp",
        pid=1234,
        user="root",
        port=8080,
        address="127.0.0.1:8080",
        is_system=False,
        is_exposed=False,
    )
    
    issues = assess_security(proc)
    
    # Should have MEDIUM for running as root
    assert any("root" in issue[1] for issue in issues)


def test_check_exposure_localhost():
    """Test exposure check for localhost-only binding."""
    proc = PortProcess(
        command="node",
        pid=1234,
        user="dev",
        port=3000,
        address="127.0.0.1:3000",
    )

    with patch("portchecker.security.check_port_accessible", return_value=False):
        is_exposed, reason = check_exposure(proc)

    assert is_exposed is False
    assert reason == "Local only"


def test_check_exposure_all_interfaces():
    """Test exposure check for all-interfaces binding."""
    proc = PortProcess(
        command="node",
        pid=1234,
        user="dev",
        port=3000,
        address="*:3000",
    )
    
    is_exposed, reason = check_exposure(proc)
    
    assert is_exposed is True
    assert "all interfaces" in reason

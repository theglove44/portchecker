"""Data models for Port Checker."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PortProcess:
    """Represents a process listening on a port."""

    command: str
    pid: int
    user: str
    port: int
    address: str
    is_system: bool = False
    app: str = ""
    project: str = "Unknown"
    fingerprint: Optional[Dict] = None
    is_exposed: bool = False
    exposure_reason: str = ""
    security_issues: List[Tuple[str, str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "command": self.command,
            "pid": self.pid,
            "user": self.user,
            "port": self.port,
            "address": self.address,
            "is_system": self.is_system,
            "app": self.app,
            "project": self.project,
            "fingerprint": self.fingerprint,
            "is_exposed": self.is_exposed,
            "exposure_reason": self.exposure_reason,
            "security_issues": self.security_issues,
        }


# Constants
SYSTEM_PROCESSES = {
    'launchd', 'systemd', 'sshd', 'httpd', 'nginx', 'apache2',
    'mysqld', 'postgresql', 'dockerd', 'kubelet', 'cron'
}
SYSTEM_USERS = {'root', 'daemon'}
RISKY_PORTS = {21, 23, 445, 3389, 5900}
RISKY_PORT_NAMES = {
    21: "FTP",
    23: "Telnet",
    445: "SMB",
    3389: "RDP",
    5900: "VNC"
}
DEV_PORTS = {3000, 3001, 4000, 5000, 5173, 8080, 9000}

# Port services mapping
PORT_SERVICES = {
    21: ('FTP', 'File Transfer'),
    22: ('SSH', 'Secure Shell'),
    23: ('Telnet', 'Unencrypted Remote'),
    25: ('SMTP', 'Mail Server'),
    53: ('DNS', 'Domain Name Service'),
    80: ('HTTP', 'Web Server'),
    110: ('POP3', 'Mail Client'),
    143: ('IMAP', 'Mail Client'),
    443: ('HTTPS', 'Secure Web'),
    445: ('SMB', 'File Sharing'),
    465: ('SMTPS', 'Secure Mail'),
    587: ('SMTP', 'Mail Submission'),
    636: ('LDAPS', 'Secure LDAP'),
    993: ('IMAPS', 'Secure IMAP'),
    995: ('POP3S', 'Secure POP3'),
    1433: ('MSSQL', 'SQL Server'),
    1521: ('Oracle', 'Database'),
    3306: ('MySQL', 'Database'),
    3389: ('RDP', 'Remote Desktop'),
    5432: ('PostgreSQL', 'Database'),
    5672: ('RabbitMQ', 'Message Queue'),
    5900: ('VNC', 'Remote Desktop'),
    5984: ('CouchDB', 'Database'),
    6379: ('Redis', 'Cache'),
    8080: ('HTTP-Alt', 'Web Server'),
    8443: ('HTTPS-Alt', 'Secure Web'),
    9000: ('PHP-FPM', 'Process Manager'),
    9200: ('Elasticsearch', 'Search'),
    27017: ('MongoDB', 'Database'),
    27018: ('MongoDB', 'Database'),
}

# Service fingerprints: (regex, service, protocol)
FINGERPRINTS = [
    (r'^HTTP/', 'HTTP', 'Web Server'),
    (r'^<html', 'HTTP', 'Web Server'),
    (r'^<!DOCTYPE', 'HTTP', 'Web Server'),
    (r'^SSH-\d+\.\d+', 'SSH', 'SSH Server'),
    (r'^[0-9\.]+MariaDB', 'MariaDB', 'Database'),
    (r'^[0-9\.]+mysql', 'MySQL', 'Database'),
    (r'^EFATAL', 'PostgreSQL', 'Database'),
    (r'ready for queries', 'PostgreSQL', 'Database'),
    (r'^-WRONGTYPE', 'Redis', 'Redis'),
    (r'^Redis', 'Redis', 'Redis'),
    (r'\+OK', 'Redis', 'Redis'),
    (r'^{"name"', 'Elasticsearch', 'Search Engine'),
    (r'"cluster_name"', 'Elasticsearch', 'Search Engine'),
    (r'^{[}]', 'MongoDB', 'Database'),
    (r'"ok"\s*:\s*1', 'MongoDB', 'Database'),
    (r'^220[\s-].*[Ff][Tt][Pp]', 'FTP', 'FTP Server'),
    (r'^220 ', 'SMTP', 'Mail Server'),
    (r'^250 SMTP', 'SMTP', 'Mail Server'),
    (r'^421 ', 'FTP', 'FTP Server'),
    (r'^\* OK', 'IMAP', 'Mail Server'),
    (r'^\+OK', 'POP3', 'Mail Server'),
]

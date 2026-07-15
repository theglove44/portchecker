"""Command-line interface for Port Checker."""

import json
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import (
    add_favorite,
    get_favorite_by_name,
    load_favorites,
    remove_favorite,
)
from .fingerprint import enrich_with_fingerprints, fingerprint_ports
from .models import PortProcess
from .process_control import can_stop_process, stop_process
from .scanner import enrich_processes, scan_ports
from .security import (
    check_exposure,
    score_color,
    score_emoji,
    security_score,
)

app = typer.Typer(help="Port Checker - View and manage running development services")
console = Console()
error_console = Console(stderr=True)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"Port Checker {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", callback=version_callback, is_eager=True
    ),
) -> None:
    """Port Checker - View and manage running development services on ports."""
    pass


@app.command()
def scan(
    show_system: bool = typer.Option(
        False, "--show-system", "-s", help="Show system services"
    ),
    json_out: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
    external: bool = typer.Option(
        False, "--external", "-e", help="Check external exposure"
    ),
    fingerprint: bool = typer.Option(
        False, "--fingerprint", "-f", help="Fingerprint services"
    ),
) -> None:
    """Scan for services listening on ports."""
    if not json_out:
        console.print("[bold blue]Scanning...[/bold blue]")

    # Scan and enrich
    processes = enrich_processes(scan_ports(), show_system)

    # Fingerprint if requested
    if fingerprint:
        console.print("[bold magenta]Fingerprinting...[/bold magenta]")
        enrich_with_fingerprints(processes)

    # Check exposure if requested
    if external:
        for proc in processes:
            proc.is_exposed, proc.exposure_reason = check_exposure(proc)

    # JSON output
    if json_out:
        print(json.dumps([p.to_dict() for p in processes], indent=2))
        return

    # Table output
    if not processes:
        console.print("[green]No services found.[/green]")
        return

    table = Table(title="Ports In Use")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Port", style="green", no_wrap=True)
    table.add_column("Service", style="magenta")
    table.add_column("App", style="yellow")
    table.add_column("Project", style="blue")

    for i, proc in enumerate(processes, 1):
        svc = proc.fingerprint.get('service', '-') if proc.fingerprint else '-'
        table.add_row(
            str(i),
            str(proc.port),
            svc,
            proc.app or proc.command,
            proc.project
        )

    console.print(table)
    console.print(f"\n[bold]Found {len(processes)} service(s).[/bold]")


@app.command()
def stop(
    service_id: Optional[int] = typer.Argument(
        None, help="Service ID from scan output"
    ),
    pid: Optional[int] = typer.Option(
        None, "--pid", help="Stop by PID directly"
    ),
    show_system: bool = typer.Option(
        False, "--show-system", help="Include system services in ID lookup"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation"
    ),
    force: bool = typer.Option(
        False, "--force", help="Force kill immediately"
    ),
) -> None:
    """Stop a service by ID or PID."""
    processes = enrich_processes(scan_ports(), True)
    visible = processes if show_system else [p for p in processes if not p.is_system]

    # Find target process
    proc: Optional[PortProcess] = None

    if pid is not None:
        proc = next((p for p in processes if p.pid == pid), None)
    elif service_id is not None:
        if 1 <= service_id <= len(visible):
            proc = visible[service_id - 1]

    if not proc:
        error_console.print("[red]Service not found.[/red]")
        raise typer.Exit(1)

    # Check if we can stop it
    can_stop, reason = can_stop_process(proc)
    if not can_stop:
        error_console.print(f"[red]{reason}[/red]")
        raise typer.Exit(1)

    # Show what we're stopping
    console.print(
        f"[yellow]Stopping:[/yellow] {proc.app} on port {proc.port} (PID: {proc.pid})"
    )

    # Confirm
    if not yes and not typer.confirm("Stop this service?"):
        console.print("[blue]Cancelled.[/blue]")
        return

    # Stop it
    success, message = stop_process(proc.pid, force=force)
    if success:
        console.print(f"[green]✓ {message}[/green]")
    else:
        error_console.print(f"[red]✗ {message}[/red]")
        raise typer.Exit(1)


@app.command()
def fingerprint(
    show_system: bool = typer.Option(
        False, "--show-system", help="Include system services"
    ),
    json_out: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Fingerprint services on ports."""
    console.print("[bold magenta]Fingerprinting...[/bold magenta]")

    processes = enrich_processes(scan_ports(), True)
    enrich_with_fingerprints(processes)

    # Filter to identified services
    results: List[Dict[str, Any]] = []
    for proc in processes:
        if proc.fingerprint and proc.fingerprint['service'] != 'Unknown':
            results.append({
                'port': proc.port,
                'process': proc.app,
                'service': proc.fingerprint['service'],
                'version': proc.fingerprint.get('version', ''),
                'banner': proc.fingerprint.get('banner', '')[:100]
            })

    if json_out:
        print(json.dumps(results, indent=2))
        return

    if not results:
        console.print("[yellow]No fingerprintable services found.[/yellow]")
        return

    # Group by service type
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        groups.setdefault(r['service'], []).append(r)

    console.print(f"\n[bold]Found {len(results)} service(s)[/bold]\n")

    for svc in sorted(groups.keys()):
        console.print(f"[bold magenta]{svc}[/bold magenta] ({len(groups[svc])})")
        t = Table(show_header=False, box=None)
        t.add_column("Port", style="cyan")
        t.add_column("Version", style="green")
        for s in groups[svc]:
            t.add_row(str(s['port']), s['version'] or '-')
        console.print(t)
        console.print("")


@app.command()
def exposed(
    show_system: bool = typer.Option(
        False, "--show-system", help="Include system services"
    ),
) -> None:
    """List ports exposed to the network."""
    console.print("[bold yellow]Scanning for exposed ports...[/bold yellow]")

    processes = enrich_processes(scan_ports(), True)
    exposed_list = []

    for proc in processes:
        proc.is_exposed, proc.exposure_reason = check_exposure(proc)
        if proc.is_exposed:
            exposed_list.append(proc)

    if not exposed_list:
        console.print("[green]✓ No exposed ports found.[/green]")
        return

    table = Table(title="⚠️ Exposed Ports")
    table.add_column("Port", style="red", no_wrap=True)
    table.add_column("App", style="magenta")
    table.add_column("Reason", style="yellow")

    shown = [p for p in exposed_list if not p.is_system or show_system]
    for proc in shown:
        table.add_row(
            str(proc.port),
            proc.app,
            proc.exposure_reason
        )

    console.print(table)
    console.print(f"\n[bold red]Found {len(shown)} exposed port(s).[/bold red]")


@app.command()
def security(
    show_system: bool = typer.Option(
        False, "--show-system", help="Include system services"
    ),
    json_out: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Run security assessment."""
    console.print("[bold yellow]Running security assessment...[/bold yellow]")

    processes = enrich_processes(scan_ports(), True)

    # Check exposure for all
    for proc in processes:
        proc.is_exposed, proc.exposure_reason = check_exposure(proc)

    # Calculate score
    score, issues = security_score(processes)
    high = sum(1 for i in issues if i[0] == 'HIGH')
    med = sum(1 for i in issues if i[0] == 'MEDIUM')
    low = sum(1 for i in issues if i[0] == 'LOW')

    if json_out:
        print(json.dumps({
            "score": score,
            "high": high,
            "medium": med,
            "low": low,
            "issues": [{"severity": s, "issue": i, "recommendation": r} for s, i, r in issues]
        }, indent=2))
        return

    # Display panel
    color = score_color(score)
    emoji = score_emoji(score)

    panel = Panel(
        f"[bold {color}]{emoji} Score: {score}/100[/bold {color}]\n\n"
        f"Services: {len(processes)}  High: {high}  Med: {med}  Low: {low}",
        title="🔒 Security Report",
        expand=False
    )
    console.print(panel)

    # Display issues by severity
    if issues:
        for sev, label in [("HIGH", "🚨"), ("MEDIUM", "⚠️"), ("LOW", "ℹ️")]:
            filtered = [i for i in issues if i[0] == sev]
            if filtered:
                console.print(f"\n[bold]{label} {sev}[/bold]")
                for _, issue, rec in filtered:
                    console.print(f"  • {issue}\n    → [cyan]{rec}[/cyan]")
    else:
        console.print("\n[green]✅ No issues found![/green]")


@app.command("fav-add")
def fav_add(
    port: int = typer.Argument(..., help="Port number"),
    name: str = typer.Argument(..., help="Friendly name"),
    note: str = typer.Option("", "--note", "-n", help="Optional note"),
) -> None:
    """Add a favorite port."""
    if add_favorite(port, name, note):
        console.print(f"[green]✓ Added '{name}' (port {port})[/green]")
    else:
        console.print(f"[yellow]Port {port} already in favorites.[/yellow]")


@app.command("fav-remove")
def fav_remove(
    identifier: str = typer.Argument(..., help="Port number or name"),
) -> None:
    """Remove a favorite by port or name."""
    if remove_favorite(identifier):
        console.print("[green]✓ Removed favorite[/green]")
    else:
        console.print(f"[red]Favorite not found: {identifier}[/red]")


@app.command("fav-list")
def fav_list(
    json_out: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """List favorite ports."""
    favs = load_favorites()

    if not favs:
        if json_out:
            print("[]")
            return
        console.print("[yellow]No favorites.[/yellow]")
        return

    if json_out:
        print(json.dumps(favs, indent=2))
        return

    table = Table(title="⭐ Favorites")
    table.add_column("#", style="cyan", no_wrap=True)
    table.add_column("Port", style="green", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Note", style="blue")

    for i, f in enumerate(favs, 1):
        table.add_row(
            str(i),
            str(f['port']),
            f['name'],
            f.get('note', '-')
        )

    console.print(table)


@app.command("fav-status")
def fav_status(
    json_out: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Check status of favorite ports."""
    favs = load_favorites()

    if not favs:
        console.print("[yellow]No favorites.[/yellow]")
        return

    processes = scan_ports()
    running_ports = {p.port for p in processes}

    results = []
    for f in favs:
        running = f['port'] in running_ports
        results.append({
            'name': f['name'],
            'port': f['port'],
            'running': running
        })

    if json_out:
        print(json.dumps(results, indent=2))
        return

    console.print("[bold]Favorite Status:[/bold]\n")
    for r in results:
        status = "[green]●[/green] RUNNING" if r['running'] else "[red]○[/red] stopped"
        console.print(f"  {status} {r['name']} (port {r['port']})")


@app.command("fav-stop")
def fav_stop(
    name: str = typer.Argument(..., help="Favorite name"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation"
    ),
) -> None:
    """Stop a service by favorite name."""
    fav = get_favorite_by_name(name)

    if not fav:
        console.print(f"[red]Favorite not found: {name}[/red]")
        raise typer.Exit(1)

    # Find process on that port
    processes = enrich_processes(scan_ports(), True)
    proc = next((p for p in processes if p.port == fav['port']), None)

    if not proc:
        console.print(f"[yellow]No service running on port {fav['port']}.[/yellow]")
        return

    # Check if stoppable
    can_stop, reason = can_stop_process(proc)
    if not can_stop:
        error_console.print(f"[red]{reason}[/red]")
        raise typer.Exit(1)

    console.print(
        f"[yellow]Stopping:[/yellow] {proc.app} on port {fav['port']}"
    )

    if not yes and not typer.confirm("Stop this service?"):
        console.print("[blue]Cancelled.[/blue]")
        return

    success, message = stop_process(proc.pid)
    if success:
        console.print(f"[green]✓ {message}[/green]")
    else:
        error_console.print(f"[red]✗ {message}[/red]")


@app.command()
def check(
    ports: List[int] = typer.Argument(..., help="Port numbers to check"),
) -> None:
    """Check specific ports."""
    console.print(f"[bold]Checking {len(ports)} port(s)...[/bold]\n")

    fps = fingerprint_ports(ports)

    table = Table(title="Port Status")
    table.add_column("Port", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Service", style="magenta")

    for port in ports:
        if port in fps:
            fp = fps[port]
            if fp['service'] != 'Unknown':
                status = "🟢 Open"
                service = fp['service']
                if fp.get('version') and fp['version'] not in ['detected', 'unidentified']:
                    service = f"{service} ({fp['version']})"
            else:
                status = "🟡 Open (unidentified)"
                service = "-"
        else:
            status, service = "🔴 Closed", "-"

        table.add_row(str(port), status, service)

    console.print(table)

"""Beautiful terminal output using the rich library."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from contextlib import contextmanager

console = Console()


def print_banner():
    """Print the UnitForge ASCII banner."""
    console.print(Panel.fit(
        "[bold cyan]⚙ UnitForge[/bold cyan]\n"
        "[dim]Open-source AI-powered test generation[/dim]",
        border_style="cyan",
    ))


def print_success(message: str):
    """Print a success message in green."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Print an error message in red."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[dim]→[/dim] {message}")


def print_job_result(job_result) -> None:
    """Print a formatted summary table of job results."""

    # Summary panel
    status_color = "green" if job_result.status == "DONE" else "red"
    console.print(Panel(
        f"[bold {status_color}]{job_result.status}[/bold {status_color}]\n"
        f"Job ID: [dim]{job_result.job_id}[/dim]\n"
        f"Modules: {job_result.total_modules} total · "
        f"[green]{job_result.passed_modules} passed[/green] · "
        f"[red]{job_result.failed_modules} failed[/red]\n"
        f"Average coverage: [bold]{job_result.average_coverage:.1f}%[/bold]",
        title="[bold]UnitForge Results[/bold]",
        border_style=status_color,
    ))

    # Per-module results table
    if job_result.results:
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
        )
        table.add_column("Module", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Coverage", justify="right")
        table.add_column("Tests")

        for result in job_result.results:
            passed = result.get("passed", False)
            coverage = result.get("coveragePercent", 0.0)
            module_name = result.get("moduleName", "unknown")
            agent_log = result.get("agentLog", "")

            status_str = "[green]PASSED[/green]" if passed else "[red]FAILED[/red]"

            if coverage > 0:
                color = "green" if coverage >= 80 else "yellow" if coverage >= 50 else "red"
                coverage_str = f"[{color}]{coverage:.0f}%[/{color}]"
            else:
                coverage_str = "[dim]N/A[/dim]"

            table.add_row(
                module_name,
                status_str,
                coverage_str,
                f"[dim]{agent_log[:50]}[/dim]",
            )

        console.print(table)


@contextmanager
def spinner(message: str):
    """Context manager for showing a spinner while work happens."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        yield

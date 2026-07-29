"""
UnitForge CLI — Command line interface for UnitForge.

Usage:
    unitforge generate ./my-project
    unitforge generate ./my-project --type python
    unitforge generate https://github.com/user/repo
    unitforge generate ./api-spec.yaml --type openapi
    unitforge status <job-id>
    unitforge download <job-id>
"""

import click
import sys
import os
from . import api_client, output


ORCHESTRATOR_URL_DEFAULT = "http://localhost:8080"


@click.group()
@click.version_option(version="0.5.0")
def cli():
    """UnitForge — AI-powered unit test generation engine.

    Automatically generates unit tests for Python and Java codebases.
    Free with Ollama (local AI) or use Claude/OpenAI API.

    GitHub: https://github.com/Akshat-Tated/UnitForge
    """
    pass


@cli.command()
@click.argument("input_path")
@click.option(
    "--type", "-t",
    type=click.Choice(["python", "java", "openapi"]),
    default="python",
    show_default=True,
    help="Type of input (python file/folder, java folder, or openapi spec)",
)
@click.option(
    "--orchestrator",
    default=ORCHESTRATOR_URL_DEFAULT,
    show_default=True,
    help="URL of the UnitForge orchestrator",
)
@click.option(
    "--download", "-d",
    is_flag=True,
    default=False,
    help="Download generated tests as a zip file when done",
)
@click.option(
    "--output-dir", "-o",
    default="./unitforge-tests",
    show_default=True,
    help="Directory to save downloaded tests (used with --download)",
)
@click.option(
    "--no-wait",
    is_flag=True,
    default=False,
    help="Submit job and exit immediately without waiting for results",
)
@click.option(
    "--timeout",
    default=1800,
    show_default=True,
    help="Maximum seconds to wait for job completion (default 1800 = 30 min)",
)
def generate(input_path, type, orchestrator, download, output_dir, no_wait, timeout):
    """Generate unit tests for a codebase or API spec.

    INPUT_PATH can be:
      - A local folder:     ./my-project
      - A local file:       ./api-spec.yaml
      - A GitHub URL:       https://github.com/user/repo

    Examples:

      unitforge generate ./my-project

      unitforge generate https://github.com/Akshat-Tated/UnitForge

      unitforge generate ./spec.yaml --type openapi

      unitforge generate ./my-project --download --output-dir ./generated-tests
    """
    output.print_banner()

    # Step 1: Run analysis engine
    output.print_info(f"Analyzing: [bold]{input_path}[/bold]")

    try:
        with output.spinner("Running analysis engine..."):
            module_map = api_client.run_analysis_engine(input_path, type)

        module_count = len(module_map.get("modules", []))
        output.print_success(f"Analysis complete — found {module_count} module(s)")

    except RuntimeError as e:
        output.print_error(f"Analysis failed: {e}")
        sys.exit(1)

    if module_count == 0:
        output.print_error("No modules found. Check that the path contains Python files.")
        sys.exit(1)

    # Step 2: Submit job to orchestrator
    output.print_info(f"Submitting job to orchestrator at {orchestrator}...")

    try:
        job_id = api_client.submit_job(
            module_map=module_map,
            input_type=type,
            input_path=input_path,
            orchestrator_url=orchestrator,
        )
        output.print_success(f"Job created: [bold cyan]{job_id}[/bold cyan]")

    except Exception as e:
        output.print_error(
            f"Failed to submit job: {e}\n"
            "Is the orchestrator running? Start it with: mvn spring-boot:run"
        )
        sys.exit(1)

    if no_wait:
        output.print_info(
            f"Job submitted. Check status with:\n"
            f"  unitforge status {job_id}"
        )
        return

    # Step 3: Wait for results
    output.print_info(
        f"Waiting for {module_count} agent(s) to generate tests...\n"
        f"[dim]Make sure the test agent is running: python agent.py[/dim]"
    )

    try:
        with output.spinner(f"Generating tests for {module_count} module(s)..."):
            result = api_client.poll_job_until_done(
                job_id=job_id,
                orchestrator_url=orchestrator,
                timeout=timeout,
            )

        output.print_job_result(result)

    except TimeoutError as e:
        output.print_error(str(e))
        sys.exit(1)
    except Exception as e:
        output.print_error(f"Error while waiting for results: {e}")
        sys.exit(1)

    # Step 4: Download if requested
    if download and result.status == "DONE":
        os.makedirs(output_dir, exist_ok=True)
        zip_path = os.path.join(output_dir, f"unitforge-tests-{job_id[:8]}.zip")

        try:
            with output.spinner("Downloading generated tests..."):
                api_client.download_tests(
                    job_id=job_id,
                    output_path=zip_path,
                    orchestrator_url=orchestrator,
                )
            output.print_success(f"Tests downloaded to: [bold]{zip_path}[/bold]")
        except Exception as e:
            output.print_error(f"Download failed: {e}")


@cli.command()
@click.argument("job_id")
@click.option(
    "--orchestrator",
    default=ORCHESTRATOR_URL_DEFAULT,
    show_default=True,
)
def status(job_id, orchestrator):
    """Check the status of a job.

    JOB_ID is the UUID returned by the generate command.

    Example:

      unitforge status abc12345-...
    """
    try:
        import requests
        job_resp = requests.get(
            f"{orchestrator}/api/jobs/{job_id}",
            timeout=10,
        )
        job_resp.raise_for_status()
        job = job_resp.json()

        status_val = job.get("status", "UNKNOWN")
        color = {
            "DONE": "green",
            "RUNNING": "blue",
            "QUEUED": "yellow",
            "FAILED": "red",
        }.get(status_val, "white")

        output.console.print(
            f"Job [cyan]{job_id[:8]}...[/cyan] — "
            f"[bold {color}]{status_val}[/bold {color}]"
        )

        if status_val == "DONE":
            output.print_info(
                f"Download tests: unitforge download {job_id}"
            )
        elif status_val == "RUNNING":
            output.print_info(
                "Tests are being generated. Re-run this command to check again."
            )

    except Exception as e:
        output.print_error(f"Failed to get status: {e}")
        sys.exit(1)


@cli.command()
@click.argument("job_id")
@click.option("--out", "-o", default=".", show_default=True,
              help="Directory to save the zip file")
@click.option(
    "--orchestrator",
    default=ORCHESTRATOR_URL_DEFAULT,
    show_default=True,
)
def download(job_id, out, orchestrator):
    """Download generated tests for a completed job.

    JOB_ID is the UUID returned by the generate command.

    Example:

      unitforge download abc12345-... --out ./my-tests
    """
    os.makedirs(out, exist_ok=True)
    zip_path = os.path.join(out, f"unitforge-tests-{job_id[:8]}.zip")

    try:
        with output.spinner("Downloading tests..."):
            api_client.download_tests(
                job_id=job_id,
                output_path=zip_path,
                orchestrator_url=orchestrator,
            )
        output.print_success(f"Saved to: [bold]{zip_path}[/bold]")
    except Exception as e:
        output.print_error(f"Download failed: {e}")
        sys.exit(1)

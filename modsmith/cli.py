"""ModSmith CLI entrypoint."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from modsmith import __version__
from modsmith.pipeline import run_pipeline

app = typer.Typer(
    name="modsmith",
    help="Forge Fabric mods from natural language.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Show the ModSmith version."""
    console.print(f"ModSmith v{__version__}")


@app.command()
def generate(
    description: str = typer.Argument(
        ...,
        help="Natural language description, e.g.: Create an apple that restores 4 hunger points when eaten",
    ),
    output: str = typer.Option(
        "./output",
        "--output", "-o",
        help="Packaging output directory (stores jar, zip, blueprint, README)",
    ),
    project_dir: str = typer.Option(
        "./generated_project",
        "--project-dir", "-p",
        help="Generated project directory (compilation workspace)",
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries", "-r",
        help="Maximum number of retries when blueprint generation/compilation fails",
    ),
) -> None:
    """Generate a complete Fabric mod from a natural language description."""
    console.print(Panel.fit(
        f"[bold cyan]ModSmith[/bold cyan]\n"
        f"Description: {description}\n"
        f"Output directory: {output}\n"
        f"Project directory: {project_dir}\n"
        f"Max retries: {max_retries}"
    ))

    try:
        results = run_pipeline(
            user_input=description,
            project_dir=Path(project_dir),
            output_dir=Path(output),
            max_retries=max_retries,
        )
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    if results is None:
        console.print("[bold red]❌ Generation failed. Please check the logs.[/bold red]")
        raise typer.Exit(code=1)

    console.print("\n[bold green]🎉 Generation succeeded![/bold green]")
    console.print(f"Output directory: [cyan]{output}[/cyan]")
    for key, path in results.items():
        console.print(f"  - {key}: [cyan]{path}[/cyan]")


if __name__ == "__main__":
    app()
"""ModSmith CLI entry point."""

import typer
from rich.console import Console

app = typer.Typer(
    name="modsmith",
    help="Forge Fabric mods from natural language.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Show ModSmith version."""
    from modsmith import __version__
    console.print(f"ModSmith v{__version__}")


@app.command()
def generate(
    description: str = typer.Argument(..., help="Natural language description of the mod"),
    output: str = typer.Option("./output", "--output", "-o", help="Output directory"),
) -> None:
    """Generate a Fabric mod from a natural language description."""
    console.print(f"[yellow]TODO:[/yellow] Generate mod from: {description}")
    console.print(f"[yellow]TODO:[/yellow] Output to: {output}")


if __name__ == "__main__":
    app()
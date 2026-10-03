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

@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Listen address"),
    port: int = typer.Option(8000, "--port", "-p", help="Listen port"),
) -> None:
    """Launch the Web UI service."""
    import uvicorn
    console.print(f"🌐 Starting Web UI: http://{host}:{port}")
    uvicorn.run("modsmith.web.app:app", host=host, port=port, reload=False)

from modsmith.llm.chat import chat_response as llm_chat_response


@app.command()
def chat(
    question: str = typer.Argument(
        None,
        help="The question to ask or the mod to make. If not provided, enter interactive dialogue mode.",
    ),
) -> None:
    """Enter Chat mode and clarify your mod requirements with ModSmith."""
    history: list[dict] = []

    def _ask(q: str) -> None:
        """Perform one Q&A turn, update history, and print the answer."""
        nonlocal history
        history.append({"role": "user", "content": q})
        try:
            answer = llm_chat_response(q, history=history[:-1])
        except Exception as e:
            console.print(f"[bold red]❌ Dialogue failed:[/bold red] {e}")
            history.pop()
            return
        history.append({"role": "assistant", "content": answer})
        console.print("\n[bold cyan]ModSmith:[/bold cyan]")
        console.print(answer)
        console.print()

    if question:
        _ask(question)
        return

    console.print(Panel.fit(
        "[bold cyan]Requirement Clarification[/bold cyan]\n"
        "Tell me what you want to make, and ModSmith will help you articulate it.\n"
        "Special commands: /quit to exit, /clear to clear history, /history to view history.",
        title="ModSmith Chat",
    ))

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            console.print("[dim]Goodbye![/dim]")
            break
        if user_input == "/clear":
            history.clear()
            console.print("[dim]History cleared.[/dim]")
            continue
        if user_input == "/history":
            if not history:
                console.print("[dim](No history yet)[/dim]")
                continue
            for msg in history:
                role = "You" if msg["role"] == "user" else "ModSmith"
                console.print(f"[bold]{role}:[/bold] {msg['content']}\n")
            continue

        _ask(user_input)
from __future__ import annotations

import json
import secrets
from pathlib import Path

import httpx
import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def init(directory: Path = Path(".")) -> None:
    """Create a secure local .env file and workspace."""
    env_path = directory / ".env"
    if env_path.exists():
        raise typer.BadParameter(f"Refusing to overwrite {env_path}")
    token = secrets.token_urlsafe(32)
    workspace = Path.home() / "VictorWorkspace"
    data_dir = Path.home() / "AppData" / "Local" / "VictorOperator"
    workspace.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    env_path.write_text(
        "\n".join(
            [
                f"VICTOR_API_TOKEN={token}",
                "VICTOR_HOST=127.0.0.1",
                "VICTOR_PORT=8765",
                f"VICTOR_WORKSPACE={workspace}",
                f"VICTOR_DATA_DIR={data_dir}",
                "OPENAI_API_KEY=",
                "VICTOR_MODEL=gpt-5.5",
                "VICTOR_ALLOWED_DOMAINS=github.com;docs.github.com;openai.com;platform.openai.com",
                "VICTOR_BROWSER_HEADLESS=false",
                "VICTOR_BROWSER_CHANNEL=chrome",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    console.print(f"[green]Created {env_path}[/green]")
    console.print(f"API token: [bold]{token}[/bold]")


@app.command()
def serve() -> None:
    """Start the local Victor Operator API and worker."""
    import uvicorn

    from .api import create_app
    from .config import Settings

    settings = Settings()
    uvicorn.run(
        create_app(settings), host=settings.host, port=settings.port, log_level="info"
    )


@app.command()
def submit(
    goal: str,
    token: str = typer.Option(..., envvar="VICTOR_API_TOKEN"),
    url: str = "http://127.0.0.1:8765",
) -> None:
    response = httpx.post(
        f"{url}/v1/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"goal": goal},
        timeout=30,
    )
    response.raise_for_status()
    console.print_json(json.dumps(response.json()))


@app.command()
def status(
    task_id: str,
    token: str = typer.Option(..., envvar="VICTOR_API_TOKEN"),
    url: str = "http://127.0.0.1:8765",
) -> None:
    response = httpx.get(
        f"{url}/v1/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    console.print_json(json.dumps(response.json()))


if __name__ == "__main__":
    app()

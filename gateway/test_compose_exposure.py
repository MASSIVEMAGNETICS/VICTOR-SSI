"""Regression guard for the local-only Docker Compose exposure boundary."""

from pathlib import Path
import re


COMPOSE_FILE = Path(__file__).resolve().parents[1] / "docker-compose.yml"
EXPECTED_BINDINGS = {
    "127.0.0.1:8080:8080",
    "127.0.0.1:5100:5100",
    "127.0.0.1:5200:5200",
    "127.0.0.1:5300:5300",
    "127.0.0.1:6379:6379",
    "127.0.0.1:7231:6333",
}


def test_every_published_compose_port_is_loopback_only() -> None:
    content = COMPOSE_FILE.read_text(encoding="utf-8")
    bindings = set(re.findall(r'^\s+-\s+"([^"\n]+)"\s*$', content, re.MULTILINE))

    assert bindings == EXPECTED_BINDINGS
    assert all(binding.startswith("127.0.0.1:") for binding in bindings)

from pathlib import Path

from victor_operator.config import Settings
from victor_operator.models import Action
from victor_operator.policy import PolicyEngine


def settings(tmp_path: Path) -> Settings:
    return Settings(
        VICTOR_API_TOKEN="x" * 32,
        VICTOR_WORKSPACE=tmp_path / "workspace",
        VICTOR_DATA_DIR=tmp_path / "data",
        VICTOR_ALLOWED_DOMAINS="github.com;openai.com",
    )


def test_blocks_workspace_escape(tmp_path: Path) -> None:
    policy = PolicyEngine(settings(tmp_path))
    decision = policy.evaluate(
        Action(tool="filesystem.read", arguments={"path": "../secret.txt"})
    )
    assert not decision.allowed


def test_blocks_destructive_shell_command(tmp_path: Path) -> None:
    policy = PolicyEngine(settings(tmp_path))
    decision = policy.evaluate(
        Action(
            tool="powershell.run",
            arguments={"command": "Remove-Item C:\\ -Recurse"},
        )
    )
    assert not decision.allowed


def test_safe_shell_read_does_not_require_approval(tmp_path: Path) -> None:
    policy = PolicyEngine(settings(tmp_path))
    decision = policy.evaluate(
        Action(tool="powershell.run", arguments={"command": "Get-ChildItem"})
    )
    assert decision.allowed and not decision.requires_approval


def test_unknown_domain_requires_approval(tmp_path: Path) -> None:
    policy = PolicyEngine(settings(tmp_path))
    decision = policy.evaluate(
        Action(tool="browser.navigate", arguments={"url": "https://example.org"})
    )
    assert decision.allowed and decision.requires_approval


def test_chained_shell_command_is_not_treated_as_safe(tmp_path: Path) -> None:
    policy = PolicyEngine(settings(tmp_path))
    decision = policy.evaluate(
        Action(
            tool="powershell.run",
            arguments={"command": "Get-ChildItem; Set-Content x.txt hacked"},
        )
    )
    assert decision.allowed and decision.requires_approval


def test_sensitive_browser_selector_requires_approval(tmp_path: Path) -> None:
    policy = PolicyEngine(settings(tmp_path))
    decision = policy.evaluate(
        Action(tool="browser.click", arguments={"selector": "button[type=submit]"})
    )
    assert decision.allowed and decision.requires_approval

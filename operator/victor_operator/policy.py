from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .config import Settings
from .models import Action, PolicyDecision, RiskLevel


BLOCKED_COMMAND_PATTERNS = [
    r"\bformat(?:\.com)?\b",
    r"\bshutdown(?:\.exe)?\b",
    r"\brestart-computer\b",
    r"\bstop-computer\b",
    r"\bclear-disk\b",
    r"\binitialize-disk\b",
    r"\bset-mppreference\b",
    r"\bdisable-windowsoptionalfeature\b",
    r"\binvoke-expression\b",
    r"\b(encodedcommand|-enc)\b",
    r"\bnet\s+user\b",
    r"\breg\s+(delete|add)\b",
    r"\bremove-item\b.*-recurse\b",
    r"\brm\b.*\b-rf\b",
]
SENSITIVE_UI_PATTERN = re.compile(
    r"(password|passcode|secret|token|delete|remove|publish|send|submit|purchase|buy|checkout|pay|transfer|confirm|account|security)",
    re.IGNORECASE,
)
SHELL_CHAIN_PATTERN = re.compile(r"[;|&\r\n]")

SAFE_COMMAND_PREFIXES = (
    "get-childitem",
    "get-content",
    "get-location",
    "test-path",
    "resolve-path",
    "select-string",
    "git status",
    "git diff",
    "git log",
    "python --version",
    "py --version",
    "node --version",
    "npm --version",
)


def action_digest(action: Action) -> str:
    normalized = json.dumps(action.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class PolicyEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _resolve_workspace_path(self, raw: str) -> Path:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = self.settings.workspace / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.settings.workspace)
        except ValueError as exc:
            raise PermissionError(f"Path escapes workspace: {resolved}") from exc
        return resolved

    def evaluate(self, action: Action) -> PolicyDecision:
        tool = action.tool.lower()
        args = action.arguments

        if tool == "finish":
            return PolicyDecision(allowed=True)

        if tool.startswith("filesystem."):
            try:
                for key in ("path", "source", "destination"):
                    if key in args:
                        self._resolve_workspace_path(str(args[key]))
            except PermissionError as exc:
                return PolicyDecision(allowed=False, risk=RiskLevel.BLOCKED, reason=str(exc))
            if tool in {"filesystem.write", "filesystem.move", "filesystem.copy"}:
                return PolicyDecision(
                    allowed=True,
                    requires_approval=bool(args.get("overwrite", False)),
                    risk=RiskLevel.MEDIUM if args.get("overwrite", False) else RiskLevel.LOW,
                    reason="Overwriting an existing artifact requires approval."
                    if args.get("overwrite", False)
                    else "Workspace-scoped reversible file operation.",
                )
            return PolicyDecision(allowed=True, reason="Read-only or additive workspace operation.")

        if tool == "powershell.run":
            command = str(args.get("command", "")).strip()
            lowered = command.lower()
            if not command:
                return PolicyDecision(allowed=False, risk=RiskLevel.BLOCKED, reason="Empty command.")
            if any(re.search(pattern, lowered) for pattern in BLOCKED_COMMAND_PATTERNS):
                return PolicyDecision(
                    allowed=False,
                    risk=RiskLevel.BLOCKED,
                    reason="Command matches a permanently blocked destructive pattern.",
                )
            if lowered.startswith(SAFE_COMMAND_PREFIXES) and not SHELL_CHAIN_PATTERN.search(command):
                return PolicyDecision(allowed=True, reason="Single read-only command allowlist match.")
            return PolicyDecision(
                allowed=True,
                requires_approval=True,
                risk=RiskLevel.HIGH,
                reason="Shell commands that can modify the machine require one-time approval.",
            )

        if tool == "browser.navigate":
            parsed = urlparse(str(args.get("url", "")))
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                return PolicyDecision(allowed=False, risk=RiskLevel.BLOCKED, reason="Invalid web URL.")
            host = parsed.hostname.lower()
            allowed = any(
                host == domain or host.endswith("." + domain)
                for domain in self.settings.allowed_domains
            )
            return PolicyDecision(
                allowed=True,
                requires_approval=not allowed,
                risk=RiskLevel.MEDIUM if not allowed else RiskLevel.LOW,
                reason="Domain is not on the unattended allowlist."
                if not allowed
                else "Allowlisted domain.",
            )

        if tool.startswith("browser."):
            if tool in {"browser.click", "browser.fill", "browser.press"}:
                ui_text = " ".join(
                    str(args.get(key, "")) for key in ("selector", "text", "key")
                )
                sensitive = bool(args.get("high_impact", False)) or bool(
                    SENSITIVE_UI_PATTERN.search(ui_text)
                )
                return PolicyDecision(
                    allowed=True,
                    requires_approval=sensitive,
                    risk=RiskLevel.HIGH if sensitive else RiskLevel.LOW,
                    reason="Sensitive or high-impact browser interaction requires one-time approval."
                    if sensitive
                    else "Routine browser interaction.",
                )
            return PolicyDecision(allowed=True, reason="Read-only browser operation.")

        if tool.startswith("windows."):
            if tool in {"windows.click", "windows.set_text", "windows.type_text", "windows.launch"}:
                ui_text = " ".join(str(value) for value in args.values())
                sensitive = bool(args.get("high_impact", False)) or bool(
                    SENSITIVE_UI_PATTERN.search(ui_text)
                )
                return PolicyDecision(
                    allowed=True,
                    requires_approval=sensitive,
                    risk=RiskLevel.HIGH if sensitive else RiskLevel.MEDIUM,
                    reason="Sensitive native UI mutation requires one-time approval."
                    if sensitive
                    else "Routine native UI mutation.",
                )
            return PolicyDecision(allowed=True, reason="Read-only native UI operation.")

        return PolicyDecision(
            allowed=False,
            risk=RiskLevel.BLOCKED,
            reason=f"Unknown tool is not permitted: {action.tool}",
        )

    def workspace_path(self, raw: str) -> Path:
        return self._resolve_workspace_path(raw)

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from typing import Any

from .config import Settings
from .models import Action, ToolResult
from .policy import PolicyEngine


class ExecutorHub:
    def __init__(self, settings: Settings, policy: PolicyEngine):
        self.settings = settings
        self.policy = policy
        self._playwright: Any = None
        self._browser_context: Any = None
        self._page: Any = None

    async def close(self) -> None:
        if self._browser_context is not None:
            await self._browser_context.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def execute(self, action: Action) -> ToolResult:
        started = time.perf_counter()
        try:
            if action.tool.startswith("filesystem."):
                result = await asyncio.to_thread(self._filesystem, action)
            elif action.tool == "powershell.run":
                result = await asyncio.to_thread(self._powershell, action)
            elif action.tool.startswith("browser."):
                result = await self._browser(action)
            elif action.tool.startswith("windows."):
                result = await asyncio.to_thread(self._windows, action)
            else:
                result = ToolResult(ok=False, error=f"No executor for {action.tool}")
        # This is an intentional fault-containment boundary: tool/plugin exceptions
        # become auditable ToolResult failures instead of killing the worker loop.
        except Exception as exc:  # noqa: BLE001
            result = ToolResult(ok=False, error=f"{type(exc).__name__}: {exc}")
        result.duration_ms = int((time.perf_counter() - started) * 1000)
        return result

    def _backup(self, path):
        if not path.exists() or not path.is_file():
            return None
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        relative = path.relative_to(self.settings.workspace)
        destination = self.settings.data_dir / "backups" / stamp / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        return str(destination)

    def _filesystem(self, action: Action) -> ToolResult:
        args = action.arguments
        tool = action.tool
        if tool == "filesystem.list":
            path = self.policy.workspace_path(str(args.get("path", ".")))
            if not path.exists():
                return ToolResult(ok=False, error=f"Path not found: {path}")
            rows = []
            for item in sorted(
                path.iterdir(), key=lambda value: (not value.is_dir(), value.name.lower())
            ):
                rows.append(
                    {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )
            return ToolResult(ok=True, output=rows, evidence=[str(path)])

        if tool == "filesystem.read":
            path = self.policy.workspace_path(str(args["path"]))
            max_chars = min(int(args.get("max_chars", 50000)), 200000)
            content = path.read_text(encoding="utf-8", errors="replace")
            return ToolResult(ok=True, output=content[:max_chars], evidence=[str(path)])

        if tool == "filesystem.mkdir":
            path = self.policy.workspace_path(str(args["path"]))
            path.mkdir(parents=True, exist_ok=True)
            return ToolResult(ok=True, output={"path": str(path)}, evidence=[str(path)])

        if tool == "filesystem.write":
            path = self.policy.workspace_path(str(args["path"]))
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and not bool(args.get("overwrite", False)):
                return ToolResult(ok=False, error="Destination exists; set overwrite=true.")
            backup = self._backup(path)
            temporary = path.with_suffix(path.suffix + ".victor.tmp")
            temporary.write_text(str(args.get("content", "")), encoding="utf-8")
            os.replace(temporary, path)
            evidence = [str(path)] + ([backup] if backup else [])
            return ToolResult(
                ok=True, output={"path": str(path), "backup": backup}, evidence=evidence
            )

        if tool in {"filesystem.copy", "filesystem.move"}:
            source = self.policy.workspace_path(str(args["source"]))
            destination = self.policy.workspace_path(str(args["destination"]))
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and not bool(args.get("overwrite", False)):
                return ToolResult(ok=False, error="Destination exists; set overwrite=true.")
            backup = self._backup(destination)
            if destination.exists():
                destination.unlink() if destination.is_file() else shutil.rmtree(destination)
            operation = shutil.copy2 if tool == "filesystem.copy" else shutil.move
            operation(source, destination)
            return ToolResult(
                ok=True,
                output={
                    "source": str(source),
                    "destination": str(destination),
                    "backup": backup,
                },
                evidence=[str(destination)] + ([backup] if backup else []),
            )

        return ToolResult(ok=False, error=f"Unknown filesystem tool: {tool}")

    def _powershell(self, action: Action) -> ToolResult:
        args = action.arguments
        cwd = self.policy.workspace_path(str(args.get("cwd", ".")))
        timeout = min(
            int(args.get("timeout_seconds", self.settings.command_timeout_seconds)),
            self.settings.command_timeout_seconds,
        )
        executable = shutil.which("pwsh") or shutil.which("powershell")
        if not executable:
            return ToolResult(ok=False, error="PowerShell was not found on PATH.")
        completed = subprocess.run(
            [
                executable,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                str(args["command"]),
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "POWERSHELL_TELEMETRY_OPTOUT": "1"},
            check=False,
        )
        output = {
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-30000:],
            "stderr": completed.stderr[-30000:],
        }
        return ToolResult(
            ok=completed.returncode == 0,
            output=output,
            error=None if completed.returncode == 0 else "Command failed.",
            evidence=[str(cwd)],
        )

    async def _ensure_browser(self) -> Any:
        if self._page is not None:
            return self._page
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        user_data = self.settings.data_dir / "browser-profile"
        launch_kwargs: dict[str, Any] = {"headless": self.settings.browser_headless}
        if self.settings.browser_channel:
            launch_kwargs["channel"] = self.settings.browser_channel
        try:
            self._browser_context = await self._playwright.chromium.launch_persistent_context(
                str(user_data), **launch_kwargs
            )
        # Browser engines expose provider-specific exception subclasses; this bounded
        # fallback only retries without an unavailable configured browser channel.
        except Exception:  # noqa: BLE001
            launch_kwargs.pop("channel", None)
            self._browser_context = await self._playwright.chromium.launch_persistent_context(
                str(user_data), **launch_kwargs
            )
        self._page = (
            self._browser_context.pages[0]
            if self._browser_context.pages
            else await self._browser_context.new_page()
        )
        return self._page

    async def _browser(self, action: Action) -> ToolResult:
        page = await self._ensure_browser()
        args = action.arguments
        if action.tool == "browser.navigate":
            response = await page.goto(
                str(args["url"]), wait_until="domcontentloaded", timeout=60000
            )
            return ToolResult(
                ok=True,
                output={"url": page.url, "status": response.status if response else None},
                evidence=[page.url],
            )
        if action.tool == "browser.click":
            await page.locator(str(args["selector"])).click(timeout=30000)
            return ToolResult(ok=True, output={"url": page.url})
        if action.tool == "browser.fill":
            await page.locator(str(args["selector"])).fill(
                str(args.get("text", "")), timeout=30000
            )
            return ToolResult(ok=True, output={"url": page.url})
        if action.tool == "browser.press":
            await page.locator(str(args["selector"])).press(str(args["key"]), timeout=30000)
            return ToolResult(ok=True, output={"url": page.url})
        if action.tool == "browser.extract_text":
            selector = str(args.get("selector", "body"))
            max_chars = min(int(args.get("max_chars", 50000)), 200000)
            text = await page.locator(selector).inner_text(timeout=30000)
            return ToolResult(ok=True, output=text[:max_chars], evidence=[page.url])
        if action.tool == "browser.screenshot":
            safe_name = (
                "".join(
                    c for c in str(args.get("name", "page")) if c.isalnum() or c in "-_"
                )
                or "page"
            )
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
            destination = self.settings.data_dir / "screenshots" / f"{stamp}-{safe_name}.png"
            await page.screenshot(
                path=str(destination), full_page=bool(args.get("full_page", True))
            )
            return ToolResult(
                ok=True,
                output={"path": str(destination), "url": page.url},
                evidence=[str(destination), page.url],
            )
        return ToolResult(ok=False, error=f"Unknown browser tool: {action.tool}")

    def _windows(self, action: Action) -> ToolResult:
        if os.name != "nt":
            return ToolResult(ok=False, error="Native Windows UI tools require Windows.")
        from PIL import ImageGrab
        from pywinauto import Application, Desktop

        args = action.arguments
        if action.tool == "windows.launch":
            command = f'"{args["executable"]}" {args.get("arguments", "")}'.strip()
            app = Application(backend="uia").start(command, timeout=30)
            return ToolResult(ok=True, output={"process": app.process})
        if action.tool == "windows.screenshot":
            safe_name = (
                "".join(
                    c
                    for c in str(args.get("name", "desktop"))
                    if c.isalnum() or c in "-_"
                )
                or "desktop"
            )
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
            destination = self.settings.data_dir / "screenshots" / f"{stamp}-{safe_name}.png"
            ImageGrab.grab(all_screens=True).save(destination)
            return ToolResult(
                ok=True, output={"path": str(destination)}, evidence=[str(destination)]
            )

        window = Desktop(backend="uia").window(title_re=str(args["window_title"]))
        window.wait("visible ready", timeout=30)
        if action.tool == "windows.type_text":
            window.set_focus()
            window.type_keys(str(args["text"]), with_spaces=True, pause=0.01)
            return ToolResult(ok=True, output={"window": window.window_text()})

        criteria = {
            key: args[key]
            for key in ("auto_id", "title", "control_type")
            if args.get(key)
        }
        control = window.child_window(**criteria)
        control.wait("visible enabled ready", timeout=30)
        if action.tool == "windows.click":
            control.click_input()
            return ToolResult(
                ok=True, output={"window": window.window_text(), "control": criteria}
            )
        if action.tool == "windows.set_text":
            control.set_edit_text(str(args["text"]))
            return ToolResult(
                ok=True, output={"window": window.window_text(), "control": criteria}
            )
        return ToolResult(ok=False, error=f"Unknown Windows tool: {action.tool}")

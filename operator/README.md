# Victor Operator

Victor Operator is a **real local digital employee runtime** for Windows 10/11. It accepts a goal, chooses or receives executable steps, applies a policy gate, operates files, PowerShell, Chrome, and native Windows UI, records every action in SQLite, pauses for high-impact approval, and only marks work complete after execution evidence exists.

## What is implemented

- FastAPI command center and browser dashboard
- Persistent SQLite task queue and audit history
- Natural-language next-action planning through the OpenAI Responses API
- Fully usable explicit JSON plans when no AI API key is configured
- Workspace-confined file read/write/copy/move/mkdir operations
- PowerShell execution with hard destructive-command blocks, timeouts, and approval gates
- Playwright Chrome automation with persistent login profile, screenshots, and text extraction
- Windows UI Automation through `pywinauto` using UIA controls instead of blind coordinates
- One-time approvals bound cryptographically to the exact pending action
- Atomic file writes and automatic backups before approved overwrites
- Windows installer, optional logon task, tests, and CI

## Install on Windows

Open PowerShell in this repository:

```powershell
cd operator
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -InstallStartupTask
```

The installer creates a virtual environment, installs dependencies, installs Chromium for Playwright, generates a strong API token, and optionally creates a per-user logon task.

Start manually:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Open `http://127.0.0.1:8765` and paste the API token printed during initialization. The token is also stored in `operator/.env` and must never be committed.

## Natural-language mode

Set `OPENAI_API_KEY` in `.env`, then enter a goal in the dashboard:

> Inspect the workspace, create a project inventory in reports/inventory.md, and include file counts and the five largest files.

The planner chooses one action at a time, observes real results, and replans. The API request is configured with `store=False`.

## Zero-API explicit mode

Victor can execute an exact plan without any model service:

```powershell
$token = "PASTE_YOUR_TOKEN"
$body = @{
  goal = "Create a verified hello artifact"
  steps = @(
    @{ tool = "filesystem.mkdir"; arguments = @{ path = "demo" } },
    @{ tool = "filesystem.write"; arguments = @{ path = "demo/hello.txt"; content = "Victor is operational." } },
    @{ tool = "filesystem.read"; arguments = @{ path = "demo/hello.txt" } }
  )
} | ConvertTo-Json -Depth 8
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/v1/tasks -Headers @{Authorization="Bearer $token"} -ContentType application/json -Body $body
```

## Security model

- The service binds to localhost by default.
- Filesystem tools are confined to `VICTOR_WORKSPACE`; traversal and outside paths are blocked.
- Destructive shell patterns are permanently denied.
- Non-read-only shell commands require approval.
- Unknown browser domains require approval.
- Sensitive browser and native UI actions require approval.
- Approval is valid only for the SHA-256 digest of the exact pending action.
- Deletion tools are intentionally absent from v0.1.
- Do not expose port 8765 directly to the public internet. For phone access, use a private encrypted overlay such as Tailscale and retain bearer-token authentication.

## API

- `GET /health`
- `POST /v1/tasks`
- `GET /v1/tasks`
- `GET /v1/tasks/{id}`
- `POST /v1/tasks/{id}/approval`
- `POST /v1/tasks/{id}/cancel`

Interactive API documentation is available at `/docs`.

## Current boundary

This is a production-capable **local execution foundation**, not unrestricted magic. Websites with CAPTCHA, hardware security keys, anti-bot controls, or unpredictable application UIs can still require human intervention. Money movement, publishing, account changes, destructive actions, and messages should stay approval-gated.

# Victor Operator

Victor Operator is a **local execution runtime** for Windows 10/11. It receives bounded executable plans, applies policy gates, operates files, PowerShell, Chrome, and native Windows UI, records every action in SQLite, pauses for high-impact approval, and only marks work complete after execution evidence exists.

## Model-sovereignty invariant

Victor Operator contains **no hosted-model cognition fallback**.

```text
VICTOR_MODEL_SOVEREIGNTY
hosted inference -> forbidden
silent cloud fallback -> forbidden
explicit authority-supplied plan -> allowed
future Victor-owned local cognition -> allowed only after provenance verification
```

A goal submitted without explicit execution steps fails closed until a Victor-owned local cognition adapter is integrated. External services may still be operated as tools/data sources through the policy layer; they do not become Victor's cognitive authority.

## What is implemented

- FastAPI command center and browser dashboard
- Persistent SQLite task queue and audit history
- Fully usable explicit JSON execution plans with no model service
- Fail-closed planner boundary when no explicit plan is supplied
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

## Explicit execution mode

Victor executes an exact plan without any model service:

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

A task containing only a natural-language goal is accepted into the durable task system but the worker fails it closed with a model-sovereignty error rather than transmitting the goal or history to a hosted inference provider.

## Future local cognition contract

A future cognition adapter may be added only if all of the following are true:

1. inference executes on an owner-controlled local substrate;
2. model/runtime provenance is inspectable;
3. no OpenAI, Anthropic, Google, Meta, Mistral, or other hosted inference fallback exists;
4. unavailable cognition causes deferral/failure rather than cloud fallback;
5. the planner emits the same bounded `Action` contract consumed by the existing policy engine;
6. tool execution, approval, verification, and audit authority remain outside the model.

This keeps cognition replaceable while execution identity, policy, evidence, and continuity remain Victor-owned.

## Security model

- The service binds to localhost by default.
- Filesystem tools are confined to `VICTOR_WORKSPACE`; traversal and outside paths are blocked.
- Destructive shell patterns are permanently denied.
- Non-read-only shell commands require approval.
- Unknown browser domains require approval.
- Sensitive browser and native UI actions require approval.
- Approval is valid only for the SHA-256 digest of the exact pending action.
- Deletion tools are intentionally absent from v0.1.
- Do not expose port 8765 directly to the public internet. For phone access, use a private encrypted overlay and retain bearer-token authentication.

## API

- `GET /health`
- `POST /v1/tasks`
- `GET /v1/tasks`
- `GET /v1/tasks/{id}`
- `POST /v1/tasks/{id}/approval`
- `POST /v1/tasks/{id}/cancel`

Interactive API documentation is available at `/docs`.

## Current boundary

This is a production-capable **local execution foundation**, not a complete autonomous cognition stack. Websites with CAPTCHA, hardware security keys, anti-bot controls, or unpredictable application UIs can still require human intervention. Money movement, publishing, account changes, destructive actions, and messages stay approval-gated.

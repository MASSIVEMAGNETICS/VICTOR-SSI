# One-Click Install Design

> Design document for the VICTOR-SSI GUI installer / wizard for Windows and macOS/Linux.

---

## Purpose

The one-click installer provides a graphical wizard that:

1. Guides users through pre-requisite checks (Docker Desktop, available RAM, disk space).
2. Clones or downloads component repositories.
3. Writes a configured `.env` file.
4. Starts the Docker Compose stack.
5. Waits for all services to pass health checks.
6. Opens the Electron desktop app (or default browser) when ready.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Operating System | Windows 10 64-bit, macOS 12, Ubuntu 20.04 | Windows 11, macOS 14, Ubuntu 22.04 |
| Docker Desktop | 4.0+ (Windows/macOS) or Docker Engine 24+ (Linux) | Latest stable |
| RAM | 8 GB | 16 GB |
| Disk Space | 20 GB free | 50 GB free |
| Internet Connection | Required (for initial image pull) | Broadband recommended |
| Git | 2.x | Latest |
| Node.js (optional) | 20+ (only for building the desktop app from source) | 20 LTS |

---

## UI Flow (Wizard Steps)

### Step 1: Welcome Screen
- Display VICTOR-SSI logo and version.
- Show summary of what will be installed.
- Button: **Next** / **Cancel**

### Step 2: Pre-requisite Check
- Automatically check:
  - [ ] Docker Desktop is installed and running
  - [ ] Docker Compose v2 available (`docker compose version`)
  - [ ] Git available
  - [ ] Available RAM >= 8 GB
  - [ ] Available disk space >= 20 GB
- Show green/red status for each check.
- If a check fails: show remediation link (e.g., "Install Docker Desktop").
- Button: **Re-check** / **Next** (only enabled if all checks pass)

### Step 3: Installation Directory
- Text field: choose install path (default: `C:\MASSIVEMAGNETICS\VICTOR-SSI` on Windows, `~/massivemagnetics/victor-ssi` on macOS/Linux).
- Button: **Browse** / **Next**

### Step 4: Component Configuration
- Checkboxes for optional components (all pre-selected):
  - [x] RAGFlow (document ingestion & retrieval)
  - [x] Conscious River (orchestration engine)
  - [x] Research Agent (multi-agent experiments)
  - [x] Redis
  - [x] Vector DB (Qdrant)
- Text fields (advanced, collapsible):
  - JWT Secret (auto-generated, editable)
  - Gateway Port (default: 8080)
  - Vector DB URL
  - Redis URL
- Button: **Next**

### Step 5: Review and Install
- Summary of choices.
- Progress bar with live log output:
  - Cloning/downloading repos...
  - Writing .env...
  - Running `docker-compose pull`...
  - Running `docker-compose up --build`...
  - Waiting for health checks...
- Button: **Install** / **Back**

### Step 6: Complete
- All services healthy: show green checkmarks.
- Button: **Open VICTOR-SSI** (launches Electron app or browser)
- Button: **View Logs** (opens log file)
- Button: **Close**

### Rollback (on failure)
- If any step fails: show error details and offer:
  - **Retry** — re-run the failed step
  - **Rollback** — stop containers and clean up the install directory
  - **View Logs** — open full installation log
  - **Open Issue** — deep-link to GitHub issue template

---

## Commands Executed Behind the Scenes

### Windows (PowerShell)

```powershell
# Step 2: Pre-requisite checks
docker --version
docker compose version
git --version
(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
(Get-PSDrive C).Free / 1GB

# Step 3: Create install directory
New-Item -ItemType Directory -Force -Path "C:\MASSIVEMAGNETICS\VICTOR-SSI"
Set-Location "C:\MASSIVEMAGNETICS\VICTOR-SSI"

# Step 4: Clone or download repos
git clone https://github.com/MASSIVEMAGNETICS/VICTOR-SSI.git .
# If bootstrapping submodules:
bash scripts/bootstrap_submodules.sh --method=clone

# Step 5: Write .env
Copy-Item .env.example .env
# Replace JWT_SECRET with generated value:
(Get-Content .env) -replace 'JWT_SECRET=.*', "JWT_SECRET=$generatedSecret" | Set-Content .env

# Step 5: Pull and build images
docker compose pull --ignore-pull-failures
docker compose up --build --detach

# Step 6: Wait for health checks
$timeout = 120
$start = Get-Date
do {
    Start-Sleep 5
    $health = (Invoke-RestMethod http://localhost:8080/health -ErrorAction SilentlyContinue).status
    $elapsed = ((Get-Date) - $start).TotalSeconds
} while ($health -ne "ok" -and $elapsed -lt $timeout)

if ($health -eq "ok") { Write-Host "VICTOR-SSI is healthy!" }
else { Write-Error "Health check timed out. Check docker compose logs." }
```

### macOS / Linux (Bash)

```bash
# Step 2: Pre-requisite checks
docker --version
docker compose version
git --version
free -g || vm_stat | grep 'Pages free'
df -h .

# Step 3: Create install directory
mkdir -p ~/massivemagnetics/victor-ssi
cd ~/massivemagnetics/victor-ssi

# Step 4: Clone repos
git clone https://github.com/MASSIVEMAGNETICS/VICTOR-SSI.git .
./scripts/bootstrap_submodules.sh --method=clone

# Step 5: Write .env
cp .env.example .env
JWT_SECRET=$(openssl rand -hex 32)
sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env

# Step 5: Pull and build
docker compose pull --ignore-pull-failures
docker compose up --build -d

# Step 6: Wait for health checks
TIMEOUT=120
ELAPSED=0
until curl -sf http://localhost:8080/health | grep -q '"ok"'; do
  sleep 5
  ELAPSED=$((ELAPSED + 5))
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "ERROR: Health check timed out."
    docker compose logs
    exit 1
  fi
done
echo "VICTOR-SSI is healthy and ready."
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| Docker Desktop not running | Service not started | Start Docker Desktop from system tray / Applications |
| Port 8080 already in use | Another service on 8080 | Stop the conflicting service or change `Gateway Port` in wizard Step 4 |
| Health check timeout | Services still starting | Wait longer; check `docker compose logs` for errors |
| Image pull fails | No internet / registry auth | Check internet connection; configure `DOCKER_REGISTRY` if using private registry |
| `docker compose` not found | Older Docker version | Update Docker Desktop to 4.x+ which includes Compose v2 |
| Insufficient RAM | Low memory | Close other applications or upgrade RAM; reduce enabled components in Step 4 |
| Git clone fails | SSH key not configured | Use HTTPS URL or add SSH key to GitHub (`ssh-add ~/.ssh/id_ed25519`) |
| Disk space error | Less than 20 GB free | Free disk space or choose a different installation directory |

---

## Rollback Steps

To fully remove the installation:

**Windows (PowerShell):**
```powershell
Set-Location "C:\MASSIVEMAGNETICS\VICTOR-SSI"
docker compose down -v --remove-orphans
Set-Location ..
Remove-Item -Recurse -Force "C:\MASSIVEMAGNETICS\VICTOR-SSI"
```

**macOS / Linux (Bash):**
```bash
cd ~/massivemagnetics/victor-ssi
docker compose down -v --remove-orphans
cd ~
rm -rf ~/massivemagnetics/victor-ssi
```

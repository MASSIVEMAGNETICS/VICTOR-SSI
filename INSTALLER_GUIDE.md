# VICTOR-SSI Installer Guide

> Step-by-step guide for end users to install and run the VICTOR-SSI Windows desktop application.

---

## Overview

VICTOR-SSI ships as a Windows NSIS installer (`.exe`) built by the GitHub Actions `windows-pack.yml` workflow. The installer bundles the Electron desktop wrapper, which connects to the locally running Docker Compose stack.

---

## Option A: Download Installer from GitHub Releases (Recommended)

1. **Go to Releases:**  
   Navigate to https://github.com/MASSIVEMAGNETICS/VICTOR-SSI/releases

2. **Download the installer:**  
   Find the latest release and download `victor-ssi-windows-installer.exe`.

3. **Run the installer:**  
   Double-click the `.exe`. If Windows SmartScreen prompts, click **"More info"** → **"Run anyway"** (the app is not yet code-signed; signing is a roadmap item).

4. **Follow the installation wizard:**  
   Accept the license, choose install directory (default: `C:\Program Files\VICTOR-SSI`), and complete installation.

5. **Launch VICTOR-SSI:**  
   Open from the Start Menu → **VICTOR-SSI**.

---

## Option B: Build from Source (Developers)

### Prerequisites
- Node.js 20+ and npm
- Git

### Steps

```powershell
# Clone the repo
git clone https://github.com/MASSIVEMAGNETICS/VICTOR-SSI.git
cd VICTOR-SSI

# Install Electron dependencies
cd desktop\electron
npm ci

# Start in development mode (no packaging)
npm start

# Build Windows distributable
npm run dist
# Output: desktop\electron\dist\victor-ssi-windows-installer.exe
```

---

## Starting and Stopping the Orchestrator

The Electron app connects to the Docker Compose stack running locally. You must start the stack before using the desktop app.

### Start the Orchestrator

**Using PowerShell:**
```powershell
cd C:\MASSIVEMAGNETICS\VICTOR-SSI
docker compose up --build -d
```

**Using the Makefile (if running in WSL or Git Bash):**
```bash
make up
```

**Check health:**
```powershell
Invoke-RestMethod http://localhost:8080/health
```

### Stop the Orchestrator

```powershell
cd C:\MASSIVEMAGNETICS\VICTOR-SSI
docker compose down
```

### Restart a Specific Service

```powershell
docker compose restart gateway
```

---

## Configuring the Gateway URL

By default the desktop app connects to `http://localhost:8080`. To change this (e.g., for a remote server):

1. Set a Windows user environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("GATEWAY_URL", "http://your-server:8080", "User")
   ```

2. Restart the desktop app.

---

## Windows Administration Tips

### Running as a Background Service

To run the Docker Compose stack as a Windows service that starts automatically:

1. Install [NSSM (Non-Sucking Service Manager)](https://nssm.cc/):
   ```powershell
   winget install NSSM.NSSM
   ```

2. Create a service:
   ```powershell
   nssm install victor-ssi-stack "docker" "compose -f C:\MASSIVEMAGNETICS\VICTOR-SSI\docker-compose.yml up"
   nssm set victor-ssi-stack AppDirectory "C:\MASSIVEMAGNETICS\VICTOR-SSI"
   nssm start victor-ssi-stack
   ```

3. Configure auto-start:
   ```powershell
   Set-Service -Name victor-ssi-stack -StartupType Automatic
   ```

### Firewall Rules

If the gateway needs to be accessible from other machines on the network:

```powershell
# Allow inbound TCP on port 8080
New-NetFirewallRule `
  -DisplayName "VICTOR-SSI Gateway" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 8080 `
  -Action Allow

# Allow inbound TCP on port 5100 (RAGFlow) — only if needed externally
New-NetFirewallRule `
  -DisplayName "VICTOR-SSI RAGFlow" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 5100 `
  -Action Allow
```

> **Security note:** Only expose the gateway port (8080) externally. Internal service ports (5100, 5200, 5300, 6379) should remain localhost-only.

### Viewing Logs

```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f gateway

# Save to file
docker compose logs > C:\MASSIVEMAGNETICS\victor-ssi.log
```

### Updating

1. Pull latest code:
   ```powershell
   cd C:\MASSIVEMAGNETICS\VICTOR-SSI
   git pull origin main
   ```

2. Rebuild and restart:
   ```powershell
   docker compose down
   docker compose up --build -d
   ```

3. Download and install the latest `.exe` from Releases if the desktop app itself was updated.

---

## Uninstalling

1. Stop the stack:
   ```powershell
   docker compose down -v
   ```

2. Uninstall the desktop app via **Settings → Apps → VICTOR-SSI → Uninstall**.

3. Optionally, remove the installation directory:
   ```powershell
   Remove-Item -Recurse -Force "C:\MASSIVEMAGNETICS\VICTOR-SSI"
   ```

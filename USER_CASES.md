# VICTOR-SSI User Cases

> Personas, workflows, and examples for the MASSIVEMAGNETICS Aether Hub platform.

---

## Personas Overview

| Persona | Role | Primary Goal |
|---------|------|-------------|
| **Researcher** | Data scientist / ML researcher | Run notebooks and experiments, ingest and query documents |
| **ML Engineer** | MLOps / platform engineer | Deploy, monitor, and maintain models and services |
| **Product Manager** | Business stakeholder | Demo flows, review results, communicate progress |
| **Operator** | DevOps / SRE | Manage infrastructure, secrets, scaling, uptime |

---

## Persona 1: Researcher

### Profile
- Writes Python notebooks, runs RL experiments, uses RAGFlow for literature review.
- Familiar with Docker but prefers not to manage infra directly.

### Typical Workflows

#### Workflow A: Ingest Documents into RAGFlow

1. Start the stack: `make up`
2. POST documents to RAGFlow ingestion API:
   ```bash
   curl -X POST http://localhost:5100/ingest \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"text": "Full paper text...", "metadata": {"source": "arxiv:2401.12345"}}'
   ```
3. Query via RAGFlow:
   ```bash
   curl http://localhost:5100/query?q=multi-agent+reinforcement+learning \
     -H "Authorization: Bearer $TOKEN"
   ```
4. Use retrieved context in a Jupyter notebook connected to the research agent.

#### Workflow B: Run a Multi-Agent Experiment

1. Start the research agent: `docker-compose up research-agent`
2. Start an experiment via the gateway:
   ```bash
   curl -X POST http://localhost:8080/orchestrator/start \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"experiment": "liquidation_sim", "params": {"steps": 1000}}'
   ```
3. Monitor status:
   ```bash
   curl http://localhost:8080/orchestrator/status \
     -H "Authorization: Bearer $TOKEN"
   ```
4. View results streamed to Redis and retrieved via API.

#### Workflow C: Explore Results via Gateway

1. Open the desktop app (Electron) or navigate to `http://localhost:8080`.
2. Browse experiment results and RAGFlow search interface.
3. Export results for notebook analysis.

---

## Persona 2: ML Engineer

### Profile
- Manages containerized services, CI/CD pipelines, model versions, and integration tests.
- Works closely with researchers to productionize experiments.

### Typical Workflows

#### Workflow A: Deploy a New Model Version

1. Update the component repo (e.g., `ragflow`) with new model artifacts.
2. Build and push image:
   ```bash
   docker build -t ghcr.io/massivemagnetics/ragflow:v1.2.0 ../ragflow
   docker push ghcr.io/massivemagnetics/ragflow:v1.2.0
   ```
3. Update `docker-compose.yml` image tag, restart service:
   ```bash
   docker-compose up -d ragflow
   ```
4. Verify health: `curl http://localhost:5100/health`

#### Workflow B: Add a New Service

1. Add service definition to `docker-compose.yml`.
2. Update `.env.example` with any new environment variables.
3. Update gateway `COMPONENTS` response if routing required.
4. Add service to CI matrix in `.github/workflows/ci.yml`.
5. Open a PR using the PR template, get CODEOWNER review.

#### Workflow C: Investigate a Service Failure

1. Check gateway health: `curl http://localhost:8080/health`
2. Inspect logs: `docker-compose logs -f conscious-river`
3. Restart failed service: `docker-compose restart conscious-river`
4. Review Redis streams for dropped messages.
5. File a bug report using the issue template.

---

## Persona 3: Product Manager

### Profile
- Non-technical; needs to run demo flows, review outputs, and report on progress.
- Uses the Electron desktop app or web UI.

### Typical Workflows

#### Workflow A: Start the Orchestrator for a Demo

1. Launch the VICTOR-SSI desktop app (installed via the Windows NSIS installer).
2. The app opens to `http://localhost:8080`.
3. Click "Start Orchestrator" (or use the API):
   ```bash
   curl -X POST http://localhost:8080/orchestrator/start \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"experiment": "demo_flow"}'
   ```
4. Watch the status dashboard update in real time.

#### Workflow B: Review Experiment Results

1. Navigate to the results endpoint in the browser: `http://localhost:8080/components`
2. View RAGFlow query results for the research topic.
3. Export data as JSON for stakeholder reports.

#### Workflow C: Share a Demo with Stakeholders

1. Record a screen capture of the desktop app running a demo flow.
2. Share the generated result JSON from the gateway.
3. Reference ROADMAP.md for next milestones to communicate timeline.

---

## Persona 4: Operator

### Profile
- DevOps/SRE responsible for uptime, scaling, secrets rotation, and disaster recovery.
- Manages production Docker/Kubernetes environments.

### Typical Workflows

#### Workflow A: Manage Infrastructure

1. Bootstrap the environment:
   ```bash
   make bootstrap
   cp .env.example .env
   # Fill in production secrets
   make up
   ```
2. Monitor service health with Docker healthchecks and Prometheus.
3. Scale a service (Compose): increase `replicas` in `docker-compose.yml`.

#### Workflow B: Rotate Secrets

1. Generate a new `JWT_SECRET`:
   ```bash
   openssl rand -hex 32
   ```
2. Update `.env` (and Kubernetes Secret / Docker Secret in production).
3. Rolling restart:
   ```bash
   docker-compose restart gateway
   ```
4. Verify: `curl http://localhost:8080/health`

#### Workflow C: Disaster Recovery

1. Stop the stack: `docker-compose down`
2. Restore Redis data volume from backup.
3. Restore Vector DB data volume or re-ingest documents.
4. Restart: `make up`
5. Verify all health endpoints respond.

#### Workflow D: Set Up Windows Desktop Runtime (Enterprise)

1. Download the latest `.exe` installer from GitHub Releases.
2. Run installer on end-user Windows machine.
3. Configure `GATEWAY_URL` via Windows environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("GATEWAY_URL", "http://your-server:8080", "User")
   ```
4. Launch VICTOR-SSI from the Start Menu.
5. Verify the gateway UI loads.

---

## Cross-Persona Example: End-to-End Research Flow

| Step | Who | Action |
|------|-----|--------|
| 1 | Operator | Deploy stack with `make up` |
| 2 | Researcher | Ingest 50 papers into RAGFlow |
| 3 | Researcher | Start multi-agent experiment via gateway |
| 4 | ML Engineer | Monitor CI build for new model version |
| 5 | Product Manager | Review experiment results in desktop app |
| 6 | ML Engineer | Deploy new model, update image tag |
| 7 | Operator | Rotate secrets, confirm uptime |
| 8 | Product Manager | Share results with stakeholders |

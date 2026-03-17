# VICTOR-SSI — Aether Hub Orchestration

> **Enterprise-grade orchestration meta-repo** that composes all MASSIVEMAGNETICS component repositories into a unified, runnable platform — locally via Docker Compose and deployable to any cloud or on-premise Kubernetes cluster.

---

## Overview

VICTOR-SSI (Aether Hub) is the orchestration layer for the MASSIVEMAGNETICS AI platform. It wires together:

| Component | Role |
|-----------|------|
| **API Gateway** (`./gateway`) | Central entrypoint, JWT auth, routing |
| **RAGFlow** (`../ragflow`) | Retrieval-Augmented Generation engine |
| **Conscious River** (`../conscious-river`) | Attention, memory & orchestration engine |
| **Research Agent** (`../Liquidation-Analysis-…`) | Multi-agent RL environment & experiment runner |
| **Redis** | Messaging, pub/sub, session cache |
| **Vector DB** | Semantic search (Qdrant placeholder; swap freely) |
| **Electron Desktop** (`./desktop/electron`) | Windows/macOS/Linux one-click runtime wrapper |

---

## Quickstart (local)

### Prerequisites
- Docker Desktop >= 4.x (with Compose v2)
- Git with SSH access to MASSIVEMAGNETICS repositories
- Node.js 20+ (only if building the desktop app)
- 8 GB RAM minimum (16 GB recommended)

### Bootstrap

```bash
# 1. Clone this orchestration repo
git clone git@github.com:MASSIVEMAGNETICS/VICTOR-SSI.git
cd VICTOR-SSI

# 2. Bootstrap component submodules (adds sibling repos)
./scripts/bootstrap_submodules.sh --method=submodule
# Or clone as sibling directories (simpler for most dev setups):
# ./scripts/bootstrap_submodules.sh --method=clone

# 3. Set up environment variables
cp .env.example .env
# Edit .env and set your JWT_SECRET, DOCKER_REGISTRY, VECTOR_DB_URL, REDIS_URL

# 4. Build and start the stack
docker-compose up --build

# 5. Verify services
curl http://localhost:8080/health       # Gateway
curl http://localhost:5100/health       # RAGFlow
curl http://localhost:5200/health       # Conscious River
curl http://localhost:5300/health       # Research Agent
```

Or use the Makefile shortcuts:

```bash
make bootstrap   # runs bootstrap_submodules.sh
make build       # docker-compose build
make up          # docker-compose up --build
make lint        # runs linters
```

---

## Architecture

```
+----------------------------------------------------------+
|                     VICTOR-SSI / Aether Hub              |
|                                                          |
|  +-----------+   +----------+   +-----------------+     |
|  |  Electron  |   | API GW   |   |  Conscious River |    |
|  |  Desktop   |-->| :8080    |-->|  :5200           |    |
|  +-----------+   +----+-----+   +-----------------+     |
|                       |                                  |
|              +--------+-------+                          |
|              |                |                          |
|        +-----v------+  +------v-----+                   |
|        |  RAGFlow   |  | Research   |                   |
|        |  :5100     |  | Agent:5300 |                   |
|        +-----+------+  +-----+------+                   |
|              |               |                          |
|         +----v---------------v----+                      |
|         |  Redis :6379            |                      |
|         |  Vector DB :7231        |                      |
|         +------------------------+                       |
+----------------------------------------------------------+
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system design.

---

## MVP Checklist

- [x] Orchestration docker-compose with all core services
- [x] API gateway stub (FastAPI, `/health`, `/components`)
- [x] CI build matrix (GitHub Actions)
- [x] Windows Electron desktop wrapper
- [x] Bootstrap script (submodule or clone)
- [x] Enterprise documentation (ARCHITECTURE, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT)
- [x] User personas and use cases (USER_CASES.md)
- [x] One-click install design (ONE_CLICK_INSTALL.md)
- [x] API contracts (API_CONTRACTS.md)
- [x] Roadmap (ROADMAP.md)
- [ ] Dockerfiles in component repos (ragflow, conscious-river, research-agent)
- [ ] Vector DB selection & configuration
- [ ] Container registry setup
- [ ] Kubernetes / Helm manifests
- [ ] RBAC and SSO integration
- [ ] Monitoring stack (Prometheus + Grafana)

---

## How to Contribute

See [CONTRIBUTING.md](./CONTRIBUTING.md) for full guidelines including:
- Branch naming conventions
- PR process and review requirements
- Code style and linting standards
- Test requirements

---

## Security and Support

- Report vulnerabilities by email to **SECURITY@massivemagnetics.com** (see [SECURITY.md](./SECURITY.md))
- Do **not** open public GitHub issues for security vulnerabilities
- For general questions and support, open a GitHub Discussion or issue

---

## Contact

- **Maintainers:** @MASSIVEMAGNETICS
- **Security:** SECURITY@massivemagnetics.com
- **Repository:** https://github.com/MASSIVEMAGNETICS/VICTOR-SSI

> **Note on Vector DB:** The default `vectordb` service uses Qdrant as a placeholder. Replace the image in `docker-compose.yml` and update `VECTOR_DB_URL` in `.env` with your preferred provider (Weaviate, Milvus, Pinecone, etc.).
>
> **Note on Registry:** Set `DOCKER_REGISTRY` in `.env` to your container registry (e.g., `ghcr.io/massivemagnetics`) before pushing images.

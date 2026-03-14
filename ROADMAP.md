# VICTOR-SSI Roadmap

> High-level roadmap for the MASSIVEMAGNETICS Aether Hub orchestration platform.

---

## Current State (This PR)

The orchestration scaffold is in place. The following are available:

- [x] Docker Compose stack (gateway, ragflow, conscious-river, research-agent, redis, vectordb)
- [x] API gateway stub (FastAPI, `/health`, `/components`)
- [x] GitHub Actions CI (build matrix, no image push)
- [x] Windows Electron desktop wrapper + build workflow
- [x] Bootstrap script (submodule or clone method)
- [x] Enterprise documentation (ARCHITECTURE, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT)
- [x] User personas and use cases
- [x] One-click install design document
- [x] API contracts
- [x] MIT License

---

## Immediate Tasks (Sprint 1)

- [ ] Add Dockerfiles to component repos (ragflow, conscious-river, research-agent)
- [ ] Choose and configure Vector DB (Qdrant default, or swap to Weaviate/Milvus)
- [ ] Add container registry (GHCR or ECR) and CI push step on merge to main
- [ ] Enable branch protection on `main` (require PR + review + passing CI)
- [ ] Add `label: scaffold` to this PR and assign to CODEOWNERS
- [ ] Add `.gitignore` and `.dockerignore` to gateway and desktop
- [ ] Generate `package-lock.json` for desktop/electron and commit

---

## Next Milestones (Q1–Q2)

### Security & Auth
- [ ] JWT validation middleware in the gateway (verify and forward tokens)
- [ ] Auth service or Keycloak/Auth0 integration for OAuth2/OIDC
- [ ] RBAC on orchestrator endpoints (admin, operator, readonly roles)
- [ ] mTLS for service-to-service communication
- [ ] Code-sign the Windows Electron installer

### Observability
- [ ] Add Prometheus + Grafana to docker-compose (metrics dashboard)
- [ ] Instrument gateway with `prometheus-fastapi-instrumentator`
- [ ] Add structured logging (JSON) to all services
- [ ] Distributed tracing with OpenTelemetry + Jaeger/Tempo

### Gateway Enhancements
- [ ] Implement `/orchestrator/start`, `/orchestrator/stop`, `/orchestrator/status` endpoints
- [ ] Request validation and error handling middleware
- [ ] Rate limiting (per API key / JWT subject)
- [ ] Circuit breaker for downstream service calls

### CI/CD Improvements
- [ ] Push Docker images to GHCR on merge to main
- [ ] Integration test job (spin up compose, run smoke tests)
- [ ] Automated dependency PRs via Dependabot (configured)
- [ ] Release workflow (tag → build → publish installer to Releases)

---

## Longer-Term Goals (Q3–Q4 and Beyond)

### Multi-Cloud Deployment
- [ ] Kubernetes manifests (Deployment, Service, Ingress, HPA)
- [ ] Helm chart for the full stack
- [ ] Terraform modules for AWS / Azure / GCP infrastructure
- [ ] Managed service adapters (ElastiCache Redis, managed Vector DB)

### Enterprise Features
- [ ] Enterprise SSO (SAML 2.0 / OIDC with Azure AD, Okta, Ping)
- [ ] Audit logging (all API calls logged with actor, action, timestamp)
- [ ] Multi-tenancy support (namespace-level isolation)
- [ ] Data encryption at rest (secrets, vector embeddings, experiment results)

### Autoscaling & Performance
- [ ] Kubernetes HPA for gateway and research-agent
- [ ] GPU node support for embedding model workers in RAGFlow
- [ ] Async job queue for long-running experiments (Celery + Redis)
- [ ] Caching layer (Redis) for frequent RAGFlow queries

### Automated Component Repo Integration
- [ ] Automated PRs to component repos adding standardized Dockerfiles
- [ ] Standardized `/health`, `/ready`, `/metrics` endpoints in all components
- [ ] Shared Python library (`victor-ssi-sdk`) for common utilities
- [ ] Component versioning and compatibility matrix

### Desktop App
- [ ] Add orchestrator control UI (start/stop/status) to Electron app
- [ ] System tray integration (show running/stopped status)
- [ ] Auto-update mechanism (electron-updater)
- [ ] Code signing for Windows and macOS

### Documentation & Developer Experience
- [ ] OpenAPI spec and API client generation
- [ ] Developer portal (docs site with docusaurus or mkdocs)
- [ ] Video walkthrough / demo recording
- [ ] Onboarding checklist for new engineers

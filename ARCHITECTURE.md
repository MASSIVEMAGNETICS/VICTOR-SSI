# VICTOR-SSI Architecture

> Detailed architecture document for the Aether Hub orchestration platform.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Components](#components)
3. [Communication Patterns](#communication-patterns)
4. [Vector DB Options](#vector-db-options)
5. [Messaging Systems](#messaging-systems)
6. [Authentication and Authorization](#authentication-and-authorization)
7. [CI/CD Flow](#cicd-flow)
8. [Observability](#observability)
9. [Secrets Management](#secrets-management)
10. [Scaling Recommendations](#scaling-recommendations)

---

## System Overview

VICTOR-SSI is an orchestration meta-repository that composes multiple specialized AI and ML services into a unified platform. Each component is independently deployable and communicates over well-defined HTTP/gRPC APIs and an event bus (Redis Streams or Kafka).

```
+--------------------+     +------------------+     +--------------------+
|  Electron Desktop  |     |  External Client  |     |  CI/CD Pipeline    |
+--------+-----------+     +--------+-----------+     +--------+-----------+
         |                          |                          |
         v                          v                          v
+--------+--------------------------+---------------------------+------------+
|                        API Gateway (FastAPI :8080)                        |
|  - JWT verification                                                       |
|  - Request routing                                                        |
|  - Rate limiting (future)                                                 |
+----+---------------------+-------------------+------------------+---------+
     |                     |                   |                  |
     v                     v                   v                  v
+----+------+    +---------+------+  +---------+------+  +--------+-------+
| RAGFlow   |    | Conscious River|  | Research Agent |  | Vector DB      |
| :5100     |    | :5200          |  | :5300          |  | :7231 (Qdrant) |
| - Ingest  |    | - Attention    |  | - Multi-agent  |  | - Embedding    |
| - Embed   |    | - Memory       |  | - RL env       |  |   store        |
| - Retrieve|    | - Orchestrate  |  | - Experiments  |  | - ANN search   |
+----+------+    +--------+-------+  +----------------+  +----------------+
     |                    |
     +--------+-----------+
              |
     +--------v-------+
     |  Redis :6379   |
     |  - Pub/Sub     |
     |  - Streams     |
     |  - Session     |
     +----------------+
```

---

## Components

### API Gateway (`./gateway`)

- **Technology:** Python 3.10, FastAPI, uvicorn
- **Responsibilities:**
  - Single ingress point for all external and desktop traffic
  - JWT token validation and forwarding of authenticated requests
  - Service discovery (returns component URLs via `/components`)
  - Health aggregation (`/health`)
  - Future: rate limiting, request logging, circuit breaking
- **Port:** 8080
- **Config:** `RAGFLOW_URL`, `CONSCIOUS_RIVER_URL`, `RESEARCH_AGENT_URL`, `JWT_SECRET`

### RAGFlow (`../ragflow`)

- **Technology:** Python (see ragflow repo for details)
- **Responsibilities:**
  - Document ingestion and chunking
  - Embedding generation (pluggable model backends)
  - Semantic retrieval and ranking
  - Feeds context to other services
- **Port:** 5100
- **Config:** `VECTOR_DB_URL`, `RAGFLOW_PORT`

### Conscious River (`../conscious-river`)

- **Technology:** Python (see conscious-river repo)
- **Responsibilities:**
  - Attention mechanism and memory management
  - Workflow/agent orchestration (coordinates tasks across services)
  - Subscribes to Redis streams for event-driven processing
- **Port:** 5200
- **Config:** `CR_PORT`, `REDIS_URL`

### Research Agent (`../Liquidation-Analysis-…`)

- **Technology:** Python (multi-agent RL)
- **Responsibilities:**
  - Runs simulation environments for trading/liquidation research
  - Exposes experiment start/stop/status API
  - Publishes results to Redis streams
- **Port:** 5300
- **Config:** `AGENT_ENV`, `REDIS_URL`

### Vector DB

- **Default:** Qdrant (`:6333` internally, mapped to `:7231` on host)
- **Alternatives:** Weaviate, Milvus, Pinecone (adapter), pgvector
- **Responsibilities:**
  - Storing and querying dense vector embeddings
  - Used by RAGFlow for semantic search

### Redis / Messaging

- **Technology:** Redis 7
- **Responsibilities:**
  - Pub/Sub for lightweight events
  - Redis Streams for durable message passing between agents
  - Session/token cache for gateway
- **Port:** 6379

### Electron Desktop Wrapper (`./desktop/electron`)

- **Technology:** Node.js, Electron, electron-builder
- **Responsibilities:**
  - Provides a native desktop window wrapping the gateway web UI
  - Bundled installer for Windows (NSIS), macOS (DMG), Linux (AppImage)
  - Configurable `GATEWAY_URL` environment variable

---

## Communication Patterns

| Pattern | Used For |
|---------|----------|
| **Synchronous REST (HTTP/JSON)** | Gateway → all services, client → gateway |
| **Redis Pub/Sub** | Lightweight notifications, real-time events |
| **Redis Streams** | Durable event log between agents (ordered, consumer groups) |
| **gRPC (future)** | High-throughput gateway → RAGFlow for large payloads |

All inter-service communication inside Docker Compose uses the Docker internal network (service names as hostnames). External access is only through the gateway on port 8080.

---

## Vector DB Options

| Option | Best For | Notes |
|--------|----------|-------|
| **Qdrant** | General purpose, easy Docker setup | Default in this scaffold |
| **Weaviate** | GraphQL querying, multi-modal | More complex setup |
| **Milvus** | Large-scale production workloads | Requires more infra |
| **pgvector** | Already using PostgreSQL | Simplest if PG is in use |
| **Pinecone** | Fully managed, cloud-native | Not self-hosted |

To swap: change the `vectordb` image in `docker-compose.yml` and update `VECTOR_DB_URL` in `.env`.

---

## Messaging Systems

The default is Redis Streams. For higher throughput and durability needs:

| Option | When to Choose |
|--------|---------------|
| **Redis Streams** | Low-to-medium throughput, simple ops, already using Redis |
| **RabbitMQ** | Complex routing, AMQP compatibility |
| **Apache Kafka** | High throughput, long retention, multi-consumer replay |
| **NATS** | Ultra-low latency, IoT/edge |

---

## Authentication and Authorization

### Current (MVP)

- **JWT Bearer tokens**: Gateway validates `Authorization: Bearer <token>` on all non-health endpoints.
- `JWT_SECRET` set via environment variable.
- Tokens generated externally (or by a future auth service).

### Recommended (Production)

1. **OAuth2 + OIDC**: Integrate with an identity provider (Keycloak, Auth0, Okta, Azure AD).
2. **Service-to-service auth**: mTLS or short-lived service tokens for internal communication.
3. **RBAC**: Role-based access on `/orchestrator/*` endpoints (admin, operator, readonly).
4. **API Keys**: For programmatic access from research scripts.

---

## CI/CD Flow

```
Developer push / PR
        |
        v
GitHub Actions (ci.yml)
  - Checkout (with submodules)
  - Matrix build: gateway, ragflow, conscious-river, research-agent
  - Docker Buildx (no push)
  - Run gateway unit tests
        |
        v
On merge to main
  - Build & push images to registry (DOCKER_REGISTRY)
  - Deploy to staging (future: Helm upgrade / docker-compose pull+up)
  - Run integration tests (future)
  - Notify (Slack / email)
        |
        v
On release tag
  - Build Windows installer (windows-pack.yml)
  - Upload .exe artifact to GitHub Release
  - Optionally trigger production deploy
```

---

## Observability

### Recommended Stack

| Tool | Purpose |
|------|---------|
| **Prometheus** | Metrics scraping from services |
| **Grafana** | Dashboards (latency, throughput, error rates) |
| **Loki** | Log aggregation |
| **Jaeger / Tempo** | Distributed tracing |

### Adding to This Stack

1. Add `prometheus` and `grafana` services to `docker-compose.yml`.
2. Instrument gateway with `prometheus-fastapi-instrumentator`.
3. Add `/metrics` endpoint to each service.
4. Configure Grafana data source pointing to Prometheus.

---

## Secrets Management

| Environment | Recommendation |
|-------------|----------------|
| **Local dev** | `.env` file (never commit) |
| **CI (GitHub Actions)** | GitHub Actions Secrets |
| **Production (Docker)** | Docker Secrets or mounted secret volumes |
| **Production (K8s)** | Kubernetes Secrets (sealed-secrets or Vault) |
| **Enterprise** | HashiCorp Vault, AWS Secrets Manager, Azure Key Vault |

---

## Scaling Recommendations

### Horizontal Scaling

- **Gateway:** Stateless; scale replicas behind a load balancer.
- **RAGFlow:** Scale read replicas; use shared Vector DB.
- **Conscious River:** Stateful; use Redis for shared state between replicas.
- **Research Agent:** Scale per experiment; use job queue (Redis/Celery).

### Vertical Scaling

- Vector DB and Redis benefit most from increased RAM.
- GPU instances recommended for embedding model workers in RAGFlow.

### Cloud Deployment

1. **Docker Compose on VM:** Simplest; suitable for small teams.
2. **Kubernetes (Helm):** Recommended for production; add HPA for auto-scaling.
3. **Managed Services:** Use managed Redis (ElastiCache / Upstash), managed Vector DB (Pinecone), managed container registry (ECR / GCR / GHCR).

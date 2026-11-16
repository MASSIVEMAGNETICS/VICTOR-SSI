# API Contracts

> Implemented API contract for the minimal VICTOR-SSI gateway.
> All endpoints are served by the API gateway at `http://127.0.0.1:8080` in the default local Compose setup.

## Current security boundary

- `gateway/app.py` currently registers only `GET /health` and `GET /components`.
- Neither route currently has authentication or authorization middleware.
- `JWT_SECRET` in `.env.example` is reserved for future authentication work; the current gateway does not read or enforce it.
- Docker Compose binds every published host port to `127.0.0.1`.
- Do not expose the gateway or component ports to a LAN/WAN or public ingress until authentication, TLS, authorization, and service-level access controls are implemented.

## Implemented endpoints

### `GET /health`

Liveness probe. Returns service status.

**Request:**
```http
GET /health HTTP/1.1
Host: 127.0.0.1:8080
```

**Response: 200 OK**
```json
{
  "status": "ok",
  "service": "gateway"
}
```

### `GET /components`

Returns configured component service URLs. This endpoint is currently unauthenticated and is intended for local development only.

**Request:**
```http
GET /components HTTP/1.1
Host: 127.0.0.1:8080
```

**Response: 200 OK**
```json
{
  "ragflow": "http://ragflow:5100",
  "conscious_river": "http://conscious-river:5200",
  "research_agent": "http://research-agent:5300"
}
```

## Planned endpoints — not implemented

The following examples are design targets only. They are not currently registered routes in `gateway/app.py` and must not be treated as available API behavior.

### `POST /orchestrator/start`

Proposed request:
```json
{
  "experiment": "liquidation_sim",
  "params": {
    "steps": 1000,
    "agents": 4,
    "seed": 42
  }
}
```

Proposed response: `202 Accepted`
```json
{
  "run_id": "run_20240314_001",
  "status": "starting",
  "experiment": "liquidation_sim",
  "started_at": "2024-03-14T20:00:00Z"
}
```

### `POST /orchestrator/stop`

Proposed request:
```json
{
  "run_id": "run_20240314_001"
}
```

Proposed response: `200 OK`
```json
{
  "run_id": "run_20240314_001",
  "status": "stopped",
  "stopped_at": "2024-03-14T20:15:00Z"
}
```

### `GET /orchestrator/status`

Proposed query parameter:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | string | No | Specific run ID. If omitted, return the most recent run. |

### Future authentication contract

JWT issuance and validation are not implemented. Add and test the authentication service and gateway middleware before changing the local-only network boundary.

## OpenAPI

When the gateway is running, FastAPI exposes its current registered routes at:

- **Swagger UI:** http://127.0.0.1:8080/docs
- **ReDoc:** http://127.0.0.1:8080/redoc
- **OpenAPI JSON:** http://127.0.0.1:8080/openapi.json

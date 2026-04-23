# Monitoring Status Page

This folder contains a separate monitoring stack for the EMQX cluster.

It runs a small FastAPI app that:

- logs in to each EMQX dashboard endpoint
- checks cluster membership through the EMQX REST API
- shows a browser status page
- exposes a JSON endpoint at `/api/status`

## Files

- `docker-compose.yml`: runs the status page as a separate stack
- `.env.example`: monitor-specific settings
- `app/`: FastAPI application

## Setup

1. Copy `.env.example` to `.env`
2. Set the correct dashboard credentials
3. Confirm the Docker network name used by the EMQX cluster

For the current cluster project, the default network name is usually:

```text
mqtt-cluster_mqtt-net
```

## Run

```bash
cd monitoring-status
cp .env.example .env
docker compose up -d --build
```

Open the page:

```text
http://localhost:8088
```

JSON status endpoint:

```text
http://localhost:8088/api/status
```

## Environment

- `STATUS_PAGE_TITLE`: page title
- `STATUS_PAGE_PORT`: local port for the monitor
- `MONITOR_TIMEOUT_SECONDS`: HTTP timeout for EMQX API calls
- `EMQX_DOCKER_NETWORK`: external Docker network shared with the EMQX cluster
- `EMQX_NODE_URLS`: comma-separated dashboard URLs reachable inside that Docker network
- `EMQX_DASHBOARD_USERNAME`: dashboard username
- `EMQX_DASHBOARD_PASSWORD`: dashboard password

## Notes

- This app uses the dashboard login API and then queries `/api/v5/nodes`, `/api/v5/nodes/{node}/stats`, and `/api/v5/nodes/{node}/metrics`.
- If the dashboard password changes, update `.env` and restart the status page.
- The monitor is intentionally separate from the main EMQX compose so you can restart or remove it without touching the broker cluster.

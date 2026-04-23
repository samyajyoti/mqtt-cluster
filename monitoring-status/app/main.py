import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates


TIMEOUT_SECONDS = float(os.getenv("MONITOR_TIMEOUT_SECONDS", "5"))
APP_TITLE = os.getenv("STATUS_PAGE_TITLE", "MQTT Cluster Status")
EMQX_USERNAME = os.getenv("EMQX_DASHBOARD_USERNAME", "")
EMQX_PASSWORD = os.getenv("EMQX_DASHBOARD_PASSWORD", "")

NODE_URLS = [
    item.strip().rstrip("/")
    for item in os.getenv(
        "EMQX_NODE_URLS",
        "http://emqx1.mqtt.local:18083,http://emqx2.mqtt.local:18084,http://emqx3.mqtt.local:18085",
    ).split(",")
    if item.strip()
]


@dataclass
class EndpointStatus:
    label: str
    base_url: str
    ok: bool
    severity: str
    message: str
    node_count: int
    expected_nodes: int
    nodes: list[dict[str, Any]]
    cluster_consistent: bool


templates = Jinja2Templates(directory="/app/templates")
app = FastAPI(title=APP_TITLE)


def endpoint_label(base_url: str) -> str:
    return base_url.replace("http://", "").replace("https://", "")


def login(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/api/v5/login",
        json={"username": EMQX_USERNAME, "password": EMQX_PASSWORD},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    token = response.json().get("token")
    if not token:
        raise ValueError("Login succeeded but no bearer token was returned.")
    return token


def get_json(base_url: str, token: str, path: str) -> Any:
    response = requests.get(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def load_endpoint_status(base_url: str) -> EndpointStatus:
    label = endpoint_label(base_url)
    try:
        token = login(base_url)
        nodes = get_json(base_url, token, "/api/v5/nodes")

        enriched_nodes: list[dict[str, Any]] = []
        for node in nodes:
            node_name = node["node"]
            encoded_name = quote(node_name, safe="")
            stats = get_json(base_url, token, f"/api/v5/nodes/{encoded_name}/stats")
            metrics = get_json(base_url, token, f"/api/v5/nodes/{encoded_name}/metrics")

            enriched_nodes.append(
                {
                    "name": node_name,
                    "status": node.get("node_status", "unknown"),
                    "role": node.get("role", "unknown"),
                    "version": node.get("version", "unknown"),
                    "uptime": node.get("uptime", 0),
                    "memory_used": node.get("memory_used", "unknown"),
                    "memory_total": node.get("memory_total", "unknown"),
                    "connections": node.get("connections", 0),
                    "live_connections": node.get("live_connections", 0),
                    "load1": node.get("load1", "n/a"),
                    "topics": stats.get("topics.count", 0),
                    "subscriptions": stats.get("subscriptions.count", 0),
                    "received_messages": metrics.get("messages.received", 0),
                    "sent_messages": metrics.get("messages.sent", 0),
                    "auth_failures": metrics.get("authentication.failure", 0),
                    "authorization_denied": metrics.get("authorization.deny", 0),
                }
            )

        expected_nodes = len(NODE_URLS)
        node_count = len(enriched_nodes)
        cluster_consistent = node_count == expected_nodes and all(
            node["status"] == "running" for node in enriched_nodes
        )

        if cluster_consistent:
            severity = "ok"
            message = f"Cluster healthy from {label}."
        else:
            severity = "warn"
            message = (
                f"{label} sees {node_count}/{expected_nodes} nodes or some nodes are not running."
            )

        return EndpointStatus(
            label=label,
            base_url=base_url,
            ok=True,
            severity=severity,
            message=message,
            node_count=node_count,
            expected_nodes=expected_nodes,
            nodes=enriched_nodes,
            cluster_consistent=cluster_consistent,
        )
    except Exception as exc:
        return EndpointStatus(
            label=label,
            base_url=base_url,
            ok=False,
            severity="error",
            message=str(exc),
            node_count=0,
            expected_nodes=len(NODE_URLS),
            nodes=[],
            cluster_consistent=False,
        )


def collect_status() -> dict[str, Any]:
    endpoints = [load_endpoint_status(base_url) for base_url in NODE_URLS]
    healthy_endpoints = sum(1 for endpoint in endpoints if endpoint.cluster_consistent)
    reachable_endpoints = sum(1 for endpoint in endpoints if endpoint.ok)

    if healthy_endpoints == len(endpoints) and endpoints:
        overall = {
            "severity": "ok",
            "message": f"All {healthy_endpoints} endpoints report a healthy cluster.",
        }
    elif reachable_endpoints:
        overall = {
            "severity": "warn",
            "message": (
                f"{reachable_endpoints}/{len(endpoints)} endpoints are reachable, "
                "but cluster state is inconsistent."
            ),
        }
    else:
        overall = {
            "severity": "error",
            "message": "No EMQX dashboard endpoints are reachable from the monitor.",
        }

    merged_nodes: dict[str, dict[str, Any]] = {}
    for endpoint in endpoints:
        for node in endpoint.nodes:
            merged_nodes[node["name"]] = node

    return {
        "title": APP_TITLE,
        "overall": overall,
        "endpoints": endpoints,
        "nodes": list(merged_nodes.values()),
    }


@app.get("/")
def status_page(request: Request):
    payload = collect_status()
    return templates.TemplateResponse(
        request=request,
        name="status.html",
        context=payload,
    )


@app.get("/api/status")
def status_api():
    payload = collect_status()
    return JSONResponse(
        {
            "title": payload["title"],
            "overall": payload["overall"],
            "nodes": payload["nodes"],
            "endpoints": [
                {
                    "label": endpoint.label,
                    "base_url": endpoint.base_url,
                    "ok": endpoint.ok,
                    "severity": endpoint.severity,
                    "message": endpoint.message,
                    "node_count": endpoint.node_count,
                    "expected_nodes": endpoint.expected_nodes,
                }
                for endpoint in payload["endpoints"]
            ],
        }
    )

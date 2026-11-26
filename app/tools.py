"""Read-only local diagnostics used by VoiceOps AI Assistant."""

from __future__ import annotations

import http.client
import json
import os
import socket
import urllib.request
import shutil
import time
from typing import Any, Dict, Tuple


TOOL_DECLARATIONS = [
    {
        "name": "check_cpu_usage",
        "description": "Check current CPU usage of the environment running the voice assistant.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "check_memory_usage",
        "description": "Check current memory usage of the environment running the voice assistant.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "check_disk_usage",
        "description": "Check disk usage for the root filesystem of the environment running the voice assistant.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "check_local_port",
        "description": "Check whether a TCP port is reachable from the voice assistant environment.",
        "parameters": {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "description": "TCP port number, for example 8080."},
                "host": {"type": "string", "description": "Hostname or IP. Defaults to localhost."},
            },
            "required": ["port"],
        },
    },
    {
        "name": "check_http_endpoint",
        "description": "Check whether an HTTP or HTTPS endpoint is reachable and report its status code.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL, for example http://host.docker.internal:8080/health."},
            },
            "required": ["url"],
        },
    },
    {
        "name": "list_docker_containers",
        "description": "List running Docker containers when the Docker Engine socket is available to this demo.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "list_all_docker_containers",
        "description": "List all Docker containers (running and stopped).",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_docker_container_logs",
        "description": "Get logs from a specific Docker container.",
        "parameters": {
            "type": "object",
            "properties": {
                "container_name": {"type": "string", "description": "Name or ID of the container."},
                "tail": {"type": "integer", "description": "Number of lines to tail. Defaults to 50."},
            },
            "required": ["container_name"],
        },
    },
    {
        "name": "get_docker_container_stats",
        "description": "Get real-time resource usage statistics for a Docker container (CPU, memory, network).",
        "parameters": {
            "type": "object",
            "properties": {
                "container_name": {"type": "string", "description": "Name or ID of the container."},
            },
            "required": ["container_name"],
        },
    },
    {
        "name": "list_docker_images",
        "description": "List all Docker images available locally.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "inspect_docker_container",
        "description": "Get detailed information about a specific Docker container.",
        "parameters": {
            "type": "object",
            "properties": {
                "container_name": {"type": "string", "description": "Name or ID of the container."},
            },
            "required": ["container_name"],
        },
    },
    {
        "name": "get_docker_container_status",
        "description": "Get the status (running, stopped, paused, etc.) of a Docker container.",
        "parameters": {
            "type": "object",
            "properties": {
                "container_name": {"type": "string", "description": "Name or ID of the container."},
            },
            "required": ["container_name"],
        },
    },
    {
        "name": "list_docker_volumes",
        "description": "List all Docker volumes.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_docker_network_info",
        "description": "Get Docker network information and connected containers.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_docker_system_info",
        "description": "Get Docker system information (version, storage, containers count, images count).",
        "parameters": {"type": "object", "properties": {}},
    },
]


def _gb(value: float) -> float:
    return round(value / (1024 ** 3), 2)


def _event(name: str, title: str, summary: str, command: str, details: str = "", ok: bool = True) -> Dict[str, Any]:
    return {
        "name": name,
        "title": title,
        "summary": summary,
        "command": command,
        "details": details,
        "ok": ok,
    }


def _read_linux_cpu_times():
    with open("/proc/stat", "r", encoding="utf-8") as fh:
        first = fh.readline().split()
    if not first or first[0] != "cpu":
        raise RuntimeError("Could not read aggregate CPU counters")
    values = [float(v) for v in first[1:]]
    idle = values[3] + (values[4] if len(values) > 4 else 0.0)
    total = sum(values)
    return idle, total


def cpu_usage() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        idle1, total1 = _read_linux_cpu_times()
        time.sleep(0.25)
        idle2, total2 = _read_linux_cpu_times()
        total_delta = total2 - total1
        idle_delta = idle2 - idle1
        usage = 0.0 if total_delta <= 0 else (1.0 - idle_delta / total_delta) * 100.0
        usage = round(max(0.0, min(100.0, usage)), 1)
        cores = os.cpu_count() or 1
        summary = f"CPU usage is {usage:.1f}% across {cores} logical cores."
        return (
            _event("check_cpu_usage", "CPU Usage", summary, "Read /proc/stat", "Read-only Linux runtime metric."),
            {"result": "ok", "cpu_percent": usage, "logical_cores": cores, "summary": summary},
        )
    except Exception as exc:
        summary = "CPU utilization could not be read from this runtime."
        return (
            _event("check_cpu_usage", "CPU Usage", summary, "Read /proc/stat", str(exc), False),
            {"result": "failed", "summary": summary},
        )


def memory_usage() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        values = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                key, raw = line.split(":", 1)
                values[key] = int(raw.strip().split()[0]) * 1024
        total = values["MemTotal"]
        available = values.get("MemAvailable", values.get("MemFree", 0))
        used = max(0, total - available)
        percent = round((used / total) * 100.0, 1) if total else 0.0
        summary = f"Memory usage is {percent:.1f}%. Used {_gb(used)} GB out of {_gb(total)} GB."
        return (
            _event("check_memory_usage", "Memory Usage", summary, "Read /proc/meminfo", "Read-only Linux runtime metric."),
            {"result": "ok", "memory_percent": percent, "used_gb": _gb(used), "total_gb": _gb(total), "summary": summary},
        )
    except Exception as exc:
        summary = "Memory utilization could not be read from this runtime."
        return (
            _event("check_memory_usage", "Memory Usage", summary, "Read /proc/meminfo", str(exc), False),
            {"result": "failed", "summary": summary},
        )


def disk_usage() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    du = shutil.disk_usage("/")
    used = du.total - du.free
    percent = round((used / du.total) * 100.0, 1) if du.total else 0.0
    summary = f"Root filesystem usage is {percent:.1f}%. Used {_gb(used)} GB out of {_gb(du.total)} GB."
    return (
        _event("check_disk_usage", "Disk Usage", summary, "shutil.disk_usage('/')", "Read-only runtime metric."),
        {"result": "ok", "disk_percent": percent, "used_gb": _gb(used), "total_gb": _gb(du.total), "summary": summary},
    )

def local_port(host: str, port: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    host = host or "localhost"
    try:
        port = int(port)
    except (TypeError, ValueError):
        port = 0
    if not (1 <= port <= 65535):
        summary = "The requested TCP port is invalid."
        return (
            _event("check_local_port", "Local Port Check", summary, f"TCP connect to {host}:{port}", "Valid ports are 1-65535.", False),
            {"result": "failed", "reachable": False, "summary": summary},
        )
    try:
        with socket.create_connection((host, port), timeout=2):
            summary = f"Port {port} on {host} is reachable."
            return (
                _event("check_local_port", "Local Port Check", summary, f"TCP connect to {host}:{port}", "TCP connection established successfully."),
                {"result": "ok", "host": host, "port": port, "reachable": True, "summary": summary},
            )
    except Exception as exc:
        summary = f"Port {port} on {host} is not reachable."
        return (
            _event("check_local_port", "Local Port Check", summary, f"TCP connect to {host}:{port}", str(exc), False),
            {"result": "failed", "host": host, "port": port, "reachable": False, "summary": summary},
        )


def http_endpoint(url: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not url.startswith(("http://", "https://")):
        summary = "Endpoint URL must begin with http:// or https://."
        return (
            _event("check_http_endpoint", "HTTP Endpoint Check", summary, f"HTTP GET {url}", "Invalid URL scheme.", False),
            {"result": "failed", "url": url, "summary": summary},
        )
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "VoiceOpsAI/1.0"})
        with urllib.request.urlopen(request, timeout=5) as response:
            code = response.getcode()
        ok = 200 <= code < 400
        summary = f"Endpoint returned HTTP {code}."
        return (
            _event("check_http_endpoint", "HTTP Endpoint Check", summary, f"HTTP GET {url}", f"Checked {url}", ok),
            {"result": "ok" if ok else "failed", "url": url, "status_code": code, "summary": summary},
        )
    except Exception as exc:
        summary = f"Endpoint check failed for {url}."
        return (
            _event("check_http_endpoint", "HTTP Endpoint Check", summary, f"HTTP GET {url}", str(exc), False),
            {"result": "failed", "url": url, "summary": summary},
        )


class UnixSocketHTTPConnection(http.client.HTTPConnection):
    """Tiny HTTP client for the Docker Engine Unix socket."""

    def __init__(self, socket_path: str):
        super().__init__("localhost", timeout=4)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


def docker_containers() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = "Docker Engine API: GET /containers/json"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        details = "Use Docker Compose with Docker Desktop/WSL2, or run the app inside WSL where /var/run/docker.sock is available."
        return _event("list_docker_containers", "Docker Containers", summary, command, details, False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        details = f"Expected socket: {socket_path}. In Compose, mount /var/run/docker.sock to enable this optional demo feature."
        return _event("list_docker_containers", "Docker Containers", summary, command, details, False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", "/containers/json")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Docker Engine returned HTTP {response.status}."
            details = body.decode("utf-8", errors="replace")[:1200]
            return _event("list_docker_containers", "Docker Containers", summary, command, details, False), {"result": "failed", "summary": summary}
        payload = json.loads(body.decode("utf-8"))
        containers = []
        for item in payload:
            names = [n.lstrip("/") for n in item.get("Names", [])]
            containers.append({
                "name": names[0] if names else item.get("Id", "")[:12],
                "image": item.get("Image", ""),
                "state": item.get("State", ""),
                "status": item.get("Status", ""),
            })
        summary = f"Found {len(containers)} running Docker container(s)."
        details = "\n".join(
            f"{c['name']} | {c['image']} | {c['status']}" for c in containers[:12]
        ) or "No running containers."
        return (
            _event("list_docker_containers", "Docker Containers", summary, command, details, True),
            {"result": "ok", "containers": containers, "summary": summary},
        )
    except Exception as exc:
        summary = "Could not query the Docker Engine socket."
        return _event("list_docker_containers", "Docker Containers", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_all_containers() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """List all containers (running and stopped)."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = "Docker Engine API: GET /containers/json?all=true"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("list_all_docker_containers", "All Docker Containers", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("list_all_docker_containers", "All Docker Containers", summary, command, "", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", "/containers/json?all=true")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Docker Engine returned HTTP {response.status}."
            return _event("list_all_docker_containers", "All Docker Containers", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        payload = json.loads(body.decode("utf-8"))
        containers = []
        for item in payload:
            names = [n.lstrip("/") for n in item.get("Names", [])]
            containers.append({
                "name": names[0] if names else item.get("Id", "")[:12],
                "image": item.get("Image", ""),
                "state": item.get("State", ""),
                "status": item.get("Status", ""),
            })
        summary = f"Found {len(containers)} total Docker container(s)."
        details = "\n".join(f"{c['name']} | {c['state']} | {c['status']}" for c in containers[:15]) or "No containers."
        return (
            _event("list_all_docker_containers", "All Docker Containers", summary, command, details, True),
            {"result": "ok", "containers": containers, "summary": summary},
        )
    except Exception as exc:
        summary = "Could not query the Docker Engine socket."
        return _event("list_all_docker_containers", "All Docker Containers", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_container_logs(container_name: str, tail: int = 50) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Get logs from a specific container."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = f"Docker Engine API: GET /containers/{container_name}/logs?tail={tail}"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("get_docker_container_logs", "Container Logs", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("get_docker_container_logs", "Container Logs", summary, command, "", False), {"result": "failed", "summary": summary}
    if not container_name:
        summary = "Container name is required."
        return _event("get_docker_container_logs", "Container Logs", summary, command, "Provide container name or ID.", False), {"result": "failed", "summary": summary}
    try:
        tail = max(1, min(int(tail), 500))
    except (TypeError, ValueError):
        tail = 50
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", f"/containers/{container_name}/logs?stdout=1&stderr=1&tail={tail}")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Could not get logs for container '{container_name}'."
            return _event("get_docker_container_logs", "Container Logs", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        logs = body.decode("utf-8", errors="replace")
        lines = logs.strip().split("\n")[-tail:]
        summary = f"Retrieved {len(lines)} log lines from '{container_name}'."
        details = "\n".join(lines)
        return (
            _event("get_docker_container_logs", "Container Logs", summary, command, details[:2000], True),
            {"result": "ok", "container": container_name, "log_lines": lines, "summary": summary},
        )
    except Exception as exc:
        summary = f"Could not retrieve logs for container '{container_name}'."
        return _event("get_docker_container_logs", "Container Logs", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_container_stats(container_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Get real-time stats for a container."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = f"Docker Engine API: GET /containers/{container_name}/stats?stream=false"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("get_docker_container_stats", "Container Stats", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("get_docker_container_stats", "Container Stats", summary, command, "", False), {"result": "failed", "summary": summary}
    if not container_name:
        summary = "Container name is required."
        return _event("get_docker_container_stats", "Container Stats", summary, command, "Provide container name or ID.", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", f"/containers/{container_name}/stats?stream=false")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Could not get stats for container '{container_name}'."
            return _event("get_docker_container_stats", "Container Stats", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        stats_data = json.loads(body.decode("utf-8"))
        
        # Extract useful stats
        cpu_percent = 0.0
        memory_mb = 0
        memory_limit_mb = 0
        try:
            cpu_delta = stats_data.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0) - stats_data.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
            system_delta = stats_data.get("cpu_stats", {}).get("system_cpu_usage", 0) - stats_data.get("precpu_stats", {}).get("system_cpu_usage", 0)
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            memory_mb = round(stats_data.get("memory_stats", {}).get("usage", 0) / (1024 * 1024), 2)
            memory_limit_mb = round(stats_data.get("memory_stats", {}).get("limit", 0) / (1024 * 1024), 2)
        except:
            pass
        
        summary = f"CPU: {cpu_percent:.1f}% | Memory: {memory_mb}MB / {memory_limit_mb}MB"
        details = f"Container: {container_name}\nCPU Usage: {cpu_percent:.2f}%\nMemory: {memory_mb}MB / {memory_limit_mb}MB"
        return (
            _event("get_docker_container_stats", "Container Stats", summary, command, details, True),
            {"result": "ok", "container": container_name, "cpu_percent": cpu_percent, "memory_mb": memory_mb, "memory_limit_mb": memory_limit_mb, "summary": summary},
        )
    except Exception as exc:
        summary = f"Could not retrieve stats for container '{container_name}'."
        return _event("get_docker_container_stats", "Container Stats", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_images() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """List all Docker images."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = "Docker Engine API: GET /images/json"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("list_docker_images", "Docker Images", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("list_docker_images", "Docker Images", summary, command, "", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", "/images/json")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Docker Engine returned HTTP {response.status}."
            return _event("list_docker_images", "Docker Images", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        payload = json.loads(body.decode("utf-8"))
        images = []
        for item in payload:
            repos = item.get("RepoTags", ["<none>"])
            size_mb = round(item.get("Size", 0) / (1024 * 1024), 2)
            images.append({
                "id": item.get("Id", "")[:12],
                "repository": repos[0] if repos and repos[0] != "<none>" else "<none>",
                "size_mb": size_mb,
                "created": item.get("Created", ""),
            })
        summary = f"Found {len(images)} Docker image(s)."
        details = "\n".join(f"{img['repository']} ({img['size_mb']}MB)" for img in images[:15])
        return (
            _event("list_docker_images", "Docker Images", summary, command, details, True),
            {"result": "ok", "images": images, "summary": summary},
        )
    except Exception as exc:
        summary = "Could not query Docker images."
        return _event("list_docker_images", "Docker Images", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_inspect_container(container_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Get detailed information about a container."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = f"Docker Engine API: GET /containers/{container_name}/json"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("inspect_docker_container", "Container Inspect", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("inspect_docker_container", "Container Inspect", summary, command, "", False), {"result": "failed", "summary": summary}
    if not container_name:
        summary = "Container name is required."
        return _event("inspect_docker_container", "Container Inspect", summary, command, "Provide container name or ID.", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", f"/containers/{container_name}/json")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Could not inspect container '{container_name}'."
            return _event("inspect_docker_container", "Container Inspect", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        data = json.loads(body.decode("utf-8"))
        
        info = {
            "id": data.get("Id", "")[:12],
            "name": data.get("Name", "").lstrip("/"),
            "image": data.get("Config", {}).get("Image", ""),
            "state": data.get("State", {}).get("Status", ""),
            "ports": list(data.get("NetworkSettings", {}).get("Ports", {}).keys()),
            "mounts": [m.get("Destination") for m in data.get("Mounts", [])],
            "env_vars": len(data.get("Config", {}).get("Env", [])),
        }
        summary = f"Container '{info['name']}' is {info['state']}."
        details = f"Name: {info['name']}\nImage: {info['image']}\nState: {info['state']}\nPorts: {', '.join(info['ports']) or 'None'}\nEnv Vars: {info['env_vars']}"
        return (
            _event("inspect_docker_container", "Container Inspect", summary, command, details, True),
            {"result": "ok", "container_info": info, "summary": summary},
        )
    except Exception as exc:
        summary = f"Could not inspect container '{container_name}'."
        return _event("inspect_docker_container", "Container Inspect", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_container_status(container_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Get container status."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = f"Docker Engine API: GET /containers/{container_name}/json"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("get_docker_container_status", "Container Status", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("get_docker_container_status", "Container Status", summary, command, "", False), {"result": "failed", "summary": summary}
    if not container_name:
        summary = "Container name is required."
        return _event("get_docker_container_status", "Container Status", summary, command, "Provide container name or ID.", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", f"/containers/{container_name}/json")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Could not get status for container '{container_name}'."
            return _event("get_docker_container_status", "Container Status", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        data = json.loads(body.decode("utf-8"))
        state = data.get("State", {})
        status = state.get("Status", "unknown")
        summary = f"Container '{container_name}' status: {status}"
        details = f"Status: {status}\nRunning: {state.get('Running', False)}\nPID: {state.get('Pid', 'N/A')}\nExitCode: {state.get('ExitCode', 'N/A')}"
        return (
            _event("get_docker_container_status", "Container Status", summary, command, details, True),
            {"result": "ok", "container": container_name, "status": status, "running": state.get("Running", False), "summary": summary},
        )
    except Exception as exc:
        summary = f"Could not get status for container '{container_name}'."
        return _event("get_docker_container_status", "Container Status", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_volumes() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """List all Docker volumes."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = "Docker Engine API: GET /volumes"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("list_docker_volumes", "Docker Volumes", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("list_docker_volumes", "Docker Volumes", summary, command, "", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", "/volumes")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Docker Engine returned HTTP {response.status}."
            return _event("list_docker_volumes", "Docker Volumes", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        data = json.loads(body.decode("utf-8"))
        volumes = []
        for vol in data.get("Volumes", []):
            volumes.append({
                "name": vol.get("Name", ""),
                "driver": vol.get("Driver", ""),
                "mount_point": vol.get("Mountpoint", ""),
            })
        summary = f"Found {len(volumes)} Docker volume(s)."
        details = "\n".join(f"{v['name']} ({v['driver']})" for v in volumes[:15])
        return (
            _event("list_docker_volumes", "Docker Volumes", summary, command, details, True),
            {"result": "ok", "volumes": volumes, "summary": summary},
        )
    except Exception as exc:
        summary = "Could not query Docker volumes."
        return _event("list_docker_volumes", "Docker Volumes", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_network_info() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Get Docker network information."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = "Docker Engine API: GET /networks"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("get_docker_network_info", "Docker Networks", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("get_docker_network_info", "Docker Networks", summary, command, "", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", "/networks")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Docker Engine returned HTTP {response.status}."
            return _event("get_docker_network_info", "Docker Networks", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        data = json.loads(body.decode("utf-8"))
        networks = []
        for net in data:
            containers = net.get("Containers", {})
            networks.append({
                "name": net.get("Name", ""),
                "driver": net.get("Driver", ""),
                "connected_containers": len(containers),
            })
        summary = f"Found {len(networks)} Docker network(s)."
        details = "\n".join(f"{n['name']} ({n['driver']}) - {n['connected_containers']} containers" for n in networks)
        return (
            _event("get_docker_network_info", "Docker Networks", summary, command, details, True),
            {"result": "ok", "networks": networks, "summary": summary},
        )
    except Exception as exc:
        summary = "Could not query Docker networks."
        return _event("get_docker_network_info", "Docker Networks", summary, command, str(exc), False), {"result": "failed", "summary": summary}


def docker_system_info() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Get Docker system information."""
    socket_path = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
    command = "Docker Engine API: GET /info"
    if os.name == "nt":
        summary = "Docker socket inspection is not enabled for native Windows execution."
        return _event("get_docker_system_info", "Docker System Info", summary, command, "", False), {"result": "failed", "summary": summary}
    if not os.path.exists(socket_path):
        summary = "Docker Engine socket is not available to the application."
        return _event("get_docker_system_info", "Docker System Info", summary, command, "", False), {"result": "failed", "summary": summary}
    try:
        connection = UnixSocketHTTPConnection(socket_path)
        connection.request("GET", "/info")
        response = connection.getresponse()
        body = response.read()
        if response.status != 200:
            summary = f"Docker Engine returned HTTP {response.status}."
            return _event("get_docker_system_info", "Docker System Info", summary, command, body.decode("utf-8", errors="replace")[:500], False), {"result": "failed", "summary": summary}
        data = json.loads(body.decode("utf-8"))
        
        info = {
            "docker_version": data.get("ServerVersion", "unknown"),
            "containers": data.get("Containers", 0),
            "containers_running": data.get("ContainersRunning", 0),
            "containers_paused": data.get("ContainersPaused", 0),
            "containers_stopped": data.get("ContainersStopped", 0),
            "images": data.get("Images", 0),
            "storage_driver": data.get("Driver", ""),
            "kernel_version": data.get("KernelVersion", ""),
            "os": data.get("OperatingSystem", ""),
        }
        summary = f"Docker {info['docker_version']}: {info['containers_running']} running, {info['containers_stopped']} stopped, {info['images']} images"
        details = f"Docker Version: {info['docker_version']}\nContainers: {info['containers']} total (Running: {info['containers_running']}, Paused: {info['containers_paused']}, Stopped: {info['containers_stopped']})\nImages: {info['images']}\nStorage Driver: {info['storage_driver']}\nOS: {info['os']}\nKernel: {info['kernel_version']}"
        return (
            _event("get_docker_system_info", "Docker System Info", summary, command, details, True),
            {"result": "ok", "system_info": info, "summary": summary},
        )
    except Exception as exc:
        summary = "Could not query Docker system info."
        return _event("get_docker_system_info", "Docker System Info", summary, command, str(exc), False), {"result": "failed", "summary": summary}



def dispatch_tool(name: str, args: dict):
    if name == "check_cpu_usage":
        return cpu_usage()
    if name == "check_memory_usage":
        return memory_usage()
    if name == "check_disk_usage":
        return disk_usage()
    if name == "check_local_port":
        return local_port(args.get("host", "localhost"), args.get("port", 0))
    if name == "check_http_endpoint":
        return http_endpoint(args.get("url", ""))
    if name == "list_docker_containers":
        return docker_containers()
    if name == "list_all_docker_containers":
        return docker_all_containers()
    if name == "get_docker_container_logs":
        return docker_container_logs(args.get("container_name", ""), args.get("tail", 50))
    if name == "get_docker_container_stats":
        return docker_container_stats(args.get("container_name", ""))
    if name == "list_docker_images":
        return docker_images()
    if name == "inspect_docker_container":
        return docker_inspect_container(args.get("container_name", ""))
    if name == "get_docker_container_status":
        return docker_container_status(args.get("container_name", ""))
    if name == "list_docker_volumes":
        return docker_volumes()
    if name == "get_docker_network_info":
        return docker_network_info()
    if name == "get_docker_system_info":
        return docker_system_info()
    summary = f"Tool '{name}' is not implemented in this local demo."
    return _event(name, "Unsupported Tool", summary, name, "Only read-only demo tools are exposed.", False), {"result": "failed", "summary": summary}

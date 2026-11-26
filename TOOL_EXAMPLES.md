# 🛠️ VoiceOps AI - Advanced Tool Development Examples

This guide provides complete, production-ready examples for creating new tools in VoiceOps AI.

---

## Table of Contents
1. [Logging Tool](#logging-tool)
2. [Troubleshooting Tool](#troubleshooting-tool)
3. [Process Monitor Tool](#process-monitor-tool)
4. [Network Diagnostics Tool](#network-diagnostics-tool)
5. [System Health Check Tool](#system-health-check-tool)
6. [Custom Integration Examples](#custom-integration-examples)

---

## Logging Tool

### Purpose
Collect and display application logs in real-time.

### Complete Implementation

**Step 1: Add to `app/tools.py`**

```python
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

# Tool Declaration
TOOL_DECLARATIONS.append({
    "name": "get_application_logs",
    "description": "Retrieve recent application logs, optionally filtered by level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    "parameters": {
        "type": "object",
        "properties": {
            "lines": {
                "type": "integer",
                "description": "Number of recent log lines to retrieve (default 50)"
            },
            "level": {
                "type": "string",
                "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "description": "Filter logs by level (optional)"
            },
            "minutes": {
                "type": "integer",
                "description": "Show logs from last N minutes (default all)"
            }
        }
    }
})

# Implementation
def get_application_logs(
    lines: int = 50,
    level: str = None,
    minutes: int = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Retrieve application logs.
    
    Args:
        lines: Number of lines to retrieve
        level: Filter by log level
        minutes: Only logs from last N minutes
    
    Returns:
        Tuple of (event_dict, result_dict)
    """
    try:
        log_file = "app.log"
        
        # Check if log file exists
        if not os.path.exists(log_file):
            return (
                _event(
                    "get_application_logs",
                    "Application Logs",
                    "No log file found",
                    "File read",
                    ok=False
                ),
                {"error": "Log file not found", "path": log_file}
            )
        
        # Read log file
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        
        # Filter by time if specified
        if minutes:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            filtered_lines = []
            
            for line in all_lines:
                try:
                    # Parse timestamp from log line
                    # Format: "2025-01-15 10:30:45,123"
                    timestamp_str = line.split(' - ')[0]
                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    
                    if log_time > cutoff_time:
                        filtered_lines.append(line)
                except (ValueError, IndexError):
                    # If parsing fails, include the line
                    filtered_lines.append(line)
            
            all_lines = filtered_lines
        
        # Filter by level if specified
        if level:
            all_lines = [l for l in all_lines if f" - {level} - " in l]
        
        # Get last N lines
        recent_logs = all_lines[-lines:]
        
        # Format for display
        log_entries = []
        for log_line in recent_logs:
            log_entries.append(log_line.strip())
        
        summary = f"Found {len(log_entries)} log entries"
        if level:
            summary += f" (level: {level})"
        if minutes:
            summary += f" from last {minutes} minutes"
        
        return (
            _event(
                "get_application_logs",
                "Application Logs",
                summary,
                "Read from app.log",
                details=f"Retrieved {len(log_entries)} of {len(all_lines)} total logs",
                ok=True
            ),
            {
                "logs": log_entries,
                "total_entries": len(log_entries),
                "log_file": log_file
            }
        )
    
    except Exception as e:
        return (
            _event(
                "get_application_logs",
                "Application Logs",
                f"Error reading logs: {str(e)}",
                "File read",
                ok=False
            ),
            {"error": str(e)}
        )
```

**Step 2: Add to dispatcher in `app/tools.py`**

```python
def dispatch_tool(name: str, args: Dict[str, Any]) -> Tuple[Dict, Dict]:
    """Dispatch tool calls to appropriate handlers."""
    
    # ... existing tools ...
    
    if name == "get_application_logs":
        lines = args.get("lines", 50)
        level = args.get("level")
        minutes = args.get("minutes")
        return get_application_logs(lines, level, minutes)
```

**Step 3: Test the tool**

```bash
# In terminal
python -c "
from app.tools import get_application_logs
event, result = get_application_logs(lines=10, level='ERROR')
print('Event:', event)
print('Result:', result)
"
```

**Step 4: Use in UI**

```
User: "Show me the last 20 error logs"
AI: Calls get_application_logs(lines=20, level='ERROR')
Result: Displays error logs in chat
```

---

## Troubleshooting Tool

### Purpose
Automated system troubleshooting and diagnostics.

### Complete Implementation

**Add to `app/tools.py`:**

```python
import subprocess
import platform

TOOL_DECLARATIONS.append({
    "name": "run_diagnostics",
    "description": "Run comprehensive system diagnostics to identify issues. Checks CPU, memory, disk, network, and running services.",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["all", "system", "network", "services", "disk"],
                "description": "Which diagnostics to run"
            }
        }
    }
})

def run_diagnostics(category: str = "all") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Run system diagnostics.
    
    Args:
        category: What to diagnose
    
    Returns:
        Tuple of (event_dict, result_dict)
    """
    try:
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "system": platform.system(),
            "issues": [],
            "warnings": [],
            "info": []
        }
        
        # System Diagnostics
        if category in ["all", "system"]:
            # CPU Check
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > 80:
                    diagnostics["warnings"].append(
                        f"⚠️ High CPU usage: {cpu_percent}%"
                    )
                diagnostics["info"].append(f"CPU: {cpu_percent}%")
            except Exception as e:
                diagnostics["issues"].append(f"CPU check failed: {str(e)}")
            
            # Memory Check
            try:
                mem = psutil.virtual_memory()
                if mem.percent > 85:
                    diagnostics["warnings"].append(
                        f"⚠️ High memory usage: {mem.percent}%"
                    )
                diagnostics["info"].append(f"Memory: {mem.percent}%")
            except Exception as e:
                diagnostics["issues"].append(f"Memory check failed: {str(e)}")
            
            # Disk Check
            try:
                disk = psutil.disk_usage('/')
                if disk.percent > 90:
                    diagnostics["issues"].append(
                        f"❌ Disk almost full: {disk.percent}%"
                    )
                elif disk.percent > 80:
                    diagnostics["warnings"].append(
                        f"⚠️ Disk space running low: {disk.percent}%"
                    )
                diagnostics["info"].append(f"Disk: {disk.percent}%")
            except Exception as e:
                diagnostics["issues"].append(f"Disk check failed: {str(e)}")
        
        # Network Diagnostics
        if category in ["all", "network"]:
            try:
                # Check internet connectivity
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                diagnostics["info"].append("✅ Internet: Connected")
            except Exception as e:
                diagnostics["issues"].append(f"❌ Internet: Disconnected ({str(e)})")
            
            # Check DNS
            try:
                socket.gethostbyname("google.com")
                diagnostics["info"].append("✅ DNS: Working")
            except Exception as e:
                diagnostics["issues"].append(f"❌ DNS: Failed ({str(e)})")
        
        # Services Check
        if category in ["all", "services"]:
            try:
                # Check if Gemini API is accessible
                import urllib.request
                urllib.request.urlopen("https://api.google.generativeai.dev", timeout=5)
                diagnostics["info"].append("✅ Gemini API: Accessible")
            except Exception as e:
                diagnostics["warnings"].append(f"⚠️ Gemini API: Unreachable")
        
        # Compile summary
        summary = f"Found {len(diagnostics['issues'])} issues, {len(diagnostics['warnings'])} warnings"
        
        if diagnostics["issues"]:
            details = "\n".join(diagnostics["issues"] + diagnostics["warnings"] + diagnostics["info"])
        else:
            details = "\n".join(diagnostics["info"])
        
        return (
            _event(
                "run_diagnostics",
                "System Diagnostics",
                summary,
                "System health check",
                details=details,
                ok=len(diagnostics["issues"]) == 0
            ),
            diagnostics
        )
    
    except Exception as e:
        return (
            _event(
                "run_diagnostics",
                "System Diagnostics",
                f"Diagnostics failed: {str(e)}",
                "System health check",
                ok=False
            ),
            {"error": str(e)}
        )
```

**Usage:**
```
User: "Run diagnostics"
AI: Calls run_diagnostics(category="all")
Result: Shows system health report
```

---

## Process Monitor Tool

### Purpose
Monitor running processes and their resource usage.

**Add to `app/tools.py`:**

```python
TOOL_DECLARATIONS.append({
    "name": "monitor_processes",
    "description": "Monitor running processes, sorted by CPU or memory usage.",
    "parameters": {
        "type": "object",
        "properties": {
            "sort_by": {
                "type": "string",
                "enum": ["cpu", "memory"],
                "description": "Sort processes by CPU or memory usage"
            },
            "limit": {
                "type": "integer",
                "description": "Number of top processes to show (default 10)"
            }
        }
    }
})

def monitor_processes(sort_by: str = "cpu", limit: int = 10) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Monitor running processes."""
    try:
        import psutil
        
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': round(proc.info['cpu_percent'], 2),
                    'memory': round(proc.info['memory_percent'], 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by requested metric
        if sort_by == "memory":
            processes.sort(key=lambda x: x['memory'], reverse=True)
        else:
            processes.sort(key=lambda x: x['cpu'], reverse=True)
        
        top_processes = processes[:limit]
        
        summary = f"Top {len(top_processes)} processes by {sort_by}"
        details = "\n".join([
            f"{p['name']}: CPU {p['cpu']}%, Memory {p['memory']}%"
            for p in top_processes
        ])
        
        return (
            _event(
                "monitor_processes",
                "Process Monitor",
                summary,
                "Query process list",
                details=details,
                ok=True
            ),
            {"processes": top_processes}
        )
    
    except Exception as e:
        return (
            _event(
                "monitor_processes",
                "Process Monitor",
                f"Error: {str(e)}",
                "Query process list",
                ok=False
            ),
            {"error": str(e)}
        )
```

---

## Network Diagnostics Tool

### Purpose
Detailed network diagnostics and connectivity checks.

**Add to `app/tools.py`:**

```python
TOOL_DECLARATIONS.append({
    "name": "network_diagnostics",
    "description": "Run network diagnostics including DNS, latency, and connectivity checks.",
    "parameters": {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "Host to ping (default: google.com)"
            }
        }
    }
})

def network_diagnostics(host: str = "google.com") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run network diagnostics."""
    try:
        import socket
        import subprocess
        
        results = {
            "host": host,
            "tests": {}
        }
        
        # DNS Resolution
        try:
            ip = socket.gethostbyname(host)
            results["tests"]["dns"] = {"status": "✅ OK", "result": ip}
        except socket.gaierror:
            results["tests"]["dns"] = {"status": "❌ FAILED", "result": "Cannot resolve host"}
        
        # Ping Test
        try:
            if platform.system() == "Windows":
                ping_cmd = ["ping", "-n", "1", host]
            else:
                ping_cmd = ["ping", "-c", "1", host]
            
            result = subprocess.run(ping_cmd, capture_output=True, timeout=5)
            if result.returncode == 0:
                results["tests"]["ping"] = {"status": "✅ OK", "result": "Host reachable"}
            else:
                results["tests"]["ping"] = {"status": "❌ FAILED", "result": "No response"}
        except Exception as e:
            results["tests"]["ping"] = {"status": "❌ ERROR", "result": str(e)}
        
        # Port Connectivity
        try:
            sock = socket.create_connection((host, 443), timeout=3)
            sock.close()
            results["tests"]["https"] = {"status": "✅ OK", "result": "HTTPS port open"}
        except Exception:
            results["tests"]["https"] = {"status": "❌ FAILED", "result": "Cannot connect to HTTPS"}
        
        summary = f"Network diagnostics for {host}"
        details = "\n".join([
            f"{test}: {results['tests'][test]['status']} - {results['tests'][test]['result']}"
            for test in results['tests']
        ])
        
        return (
            _event(
                "network_diagnostics",
                "Network Diagnostics",
                summary,
                "Network connectivity check",
                details=details,
                ok=all("✅" in results['tests'][t]['status'] for t in results['tests'])
            ),
            results
        )
    
    except Exception as e:
        return (
            _event(
                "network_diagnostics",
                "Network Diagnostics",
                f"Error: {str(e)}",
                "Network check",
                ok=False
            ),
            {"error": str(e)}
        )
```

---

## System Health Check Tool

### Purpose
Complete system health overview.

**Add to `app/tools.py`:**

```python
TOOL_DECLARATIONS.append({
    "name": "system_health_check",
    "description": "Get comprehensive system health status including CPU, memory, disk, temperature, and uptime.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
})

def system_health_check() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Check overall system health."""
    try:
        import psutil
        
        health = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "components": {}
        }
        
        # CPU Health
        cpu_percent = psutil.cpu_percent(interval=1)
        health["components"]["cpu"] = {
            "usage_percent": cpu_percent,
            "cores": psutil.cpu_count(),
            "status": "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
        }
        
        # Memory Health
        mem = psutil.virtual_memory()
        health["components"]["memory"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "usage_percent": mem.percent,
            "status": "healthy" if mem.percent < 80 else "warning" if mem.percent < 90 else "critical"
        }
        
        # Disk Health
        disk = psutil.disk_usage('/')
        health["components"]["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "usage_percent": disk.percent,
            "status": "healthy" if disk.percent < 80 else "warning" if disk.percent < 90 else "critical"
        }
        
        # Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        health["components"]["uptime"] = {
            "days": uptime.days,
            "hours": uptime.seconds // 3600,
            "status": "healthy"
        }
        
        # Overall status
        statuses = [c["status"] for c in health["components"].values()]
        if "critical" in statuses:
            health["status"] = "critical"
        elif "warning" in statuses:
            health["status"] = "warning"
        
        summary = f"System Health: {health['status'].upper()}"
        details = f"CPU: {cpu_percent}% | Memory: {mem.percent}% | Disk: {disk.percent}% | Uptime: {uptime.days}d {uptime.seconds // 3600}h"
        
        return (
            _event(
                "system_health_check",
                "System Health",
                summary,
                "System metrics collection",
                details=details,
                ok=health["status"] != "critical"
            ),
            health
        )
    
    except Exception as e:
        return (
            _event(
                "system_health_check",
                "System Health",
                f"Error: {str(e)}",
                "System check",
                ok=False
            ),
            {"error": str(e)}
        )
```

---

## Custom Integration Examples

### Example 1: Slack Notifications

```python
TOOL_DECLARATIONS.append({
    "name": "send_slack_notification",
    "description": "Send a notification to Slack channel.",
    "parameters": {
        "type": "object",
        "properties": {
            "channel": {
                "type": "string",
                "description": "Slack channel (e.g., #devops)"
            },
            "message": {
                "type": "string",
                "description": "Message to send"
            }
        },
        "required": ["channel", "message"]
    }
})

def send_slack_notification(channel: str, message: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Send Slack notification."""
    try:
        import os
        import requests
        
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            raise ValueError("SLACK_WEBHOOK_URL not set")
        
        payload = {
            "channel": channel,
            "text": message
        }
        
        response = requests.post(webhook_url, json=payload)
        
        return (
            _event(
                "send_slack_notification",
                "Slack Notification",
                f"Sent to {channel}",
                "HTTP POST to Slack",
                ok=response.status_code == 200
            ),
            {"status": "sent", "channel": channel}
        )
    
    except Exception as e:
        return (
            _event(
                "send_slack_notification",
                "Slack Notification",
                f"Error: {str(e)}",
                "HTTP POST",
                ok=False
            ),
            {"error": str(e)}
        )
```

---

## Testing Your Tools

### Unit Testing Template

```python
# tests/test_tools.py

import pytest
from app.tools import (
    get_application_logs,
    run_diagnostics,
    monitor_processes,
    network_diagnostics,
    system_health_check
)

def test_application_logs():
    event, result = get_application_logs(lines=5)
    assert event["name"] == "get_application_logs"
    assert "logs" in result

def test_diagnostics():
    event, result = run_diagnostics(category="system")
    assert event["name"] == "run_diagnostics"
    assert "issues" in result or "info" in result

def test_process_monitor():
    event, result = monitor_processes(limit=5)
    assert event["name"] == "monitor_processes"
    assert len(result["processes"]) <= 5

def test_network_diagnostics():
    event, result = network_diagnostics(host="google.com")
    assert event["name"] == "network_diagnostics"
    assert "tests" in result

def test_system_health():
    event, result = system_health_check()
    assert event["name"] == "system_health_check"
    assert "components" in result
```

**Run tests:**
```bash
pytest tests/test_tools.py -v
```

---

## Best Practices for Tool Development

1. **Error Handling**
   - Always wrap in try/except
   - Return meaningful error messages
   - Set `ok=False` on errors

2. **Performance**
   - Use timeouts for external calls
   - Cache results when appropriate
   - Avoid blocking operations

3. **Documentation**
   - Write clear docstrings
   - Document parameters and returns
   - Add examples to tool declaration

4. **Testing**
   - Write unit tests
   - Test error cases
   - Verify on different OS

5. **Security**
   - Validate inputs
   - Use environment variables for secrets
   - Avoid shell injection

---

**Happy tool building! 🛠️**

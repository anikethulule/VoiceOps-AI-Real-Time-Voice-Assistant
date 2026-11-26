# 🚀 VoiceOps AI - Complete Developer Guide

## Table of Contents
1. [Setup & Installation](#setup--installation)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [How to Add New Features](#how-to-add-new-features)
5. [Adding New Tools](#adding-new-tools)
6. [Frontend Integration](#frontend-integration)
7. [Logging & Debugging](#logging--debugging)
8. [Troubleshooting](#troubleshooting)
9. [Deployment](#deployment)

---

## Setup & Installation

### Prerequisites
```
✓ Python 3.9+
✓ pip (Python package manager)
✓ Git (for version control)
✓ Modern browser (Chrome, Firefox, Edge, Safari)
✓ Terminal/Command Prompt
✓ Code editor (VS Code recommended)
```

### Step 1: Clone/Navigate to Repository
```bash
cd "VoiceOps AI - Real-Time Voice Assistant"
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup Environment Variables
```bash
# Create .env file
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux

# Edit .env and add your API key:
GOOGLE_API_KEY=your_api_key_here
LOG_LEVEL=INFO
LIVE_MODEL=gemini-3.8-live
LIVE_VOICE=Aoede
```

### Step 5: Get Google API Key
1. Visit: https://ai.google.dev/
2. Sign in with Google account
3. Click "Get API Key"
4. Create new project (or select existing)
5. Generate API key
6. Copy and paste into `.env` file

### Step 6: Run the Application
```bash
# Using uvicorn directly
python -m uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

# Or with custom settings
python -m uvicorn app.server:app --host 127.0.0.1 --port 8001 --log-level debug
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 7: Open in Browser
```
http://localhost:8000
```

You should see the professional VoiceOps AI UI! ✅

---

## Architecture Overview

### System Components

```
┌──────────────────────────────────────────────────────────┐
│                        Browser (UI)                       │
│  ┌────────────────────────────────────────────────────┐  │
│  │  HTML/CSS/JavaScript - Professional Dark UI       │  │
│  │  • Sidebar with chat history                      │  │
│  │  • Message bubbles                                │  │
│  │  • Voice recording                                │  │
│  │  • Status indicators                              │  │
│  └────────────────────────────────────────────────────┘  │
│                        ↓ WebSocket                        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python)               │
│  ┌────────────────────────────────────────────────────┐  │
│  │  app/server.py - Main FastAPI Application          │  │
│  │  • Handles WebSocket connections                 │  │
│  │  • Routes requests to Gemini API                 │  │
│  │  • Manages tool calls                            │  │
│  └────────────────────────────────────────────────────┘  │
│                        ↓ gRPC                             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              Google Gemini Live API (Cloud)              │
│  • Natural language processing                           │
│  • Function/Tool calling                                 │
│  • Voice transcription & synthesis                       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   Backend Tools (Python)                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │  app/tools.py - System Information Tools          │  │
│  │  • check_cpu_usage()                              │  │
│  │  • check_memory_usage()                           │  │
│  │  • check_disk_usage()                             │  │
│  │  • check_local_port()                             │  │
│  │  • check_http_endpoint()                          │  │
│  │  • list_docker_containers()                       │  │
│  └────────────────────────────────────────────────────┘  │
│                        ↓                                  │
│              System Information Sources                   │
│  • /proc/stat (CPU on Linux)                             │
│  • /proc/meminfo (Memory on Linux)                       │
│  • shutil.disk_usage() (Disk)                            │
│  • socket (Network ports)                                │
│  • urllib (HTTP endpoints)                               │
│  • Docker socket (Containers)                            │
└──────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
User Input (Text/Voice)
       ↓
Browser WebSocket
       ↓
FastAPI /ws endpoint
       ↓
Gemini Live Session
       ├─ Analyze user input
       └─ Determine if tool needed
              ↓
       ┌──────────────────┐
       │ Tool Needed?     │
       └──────────────────┘
            ↙      ↘
          NO      YES
           ↓        ↓
      Generate   Dispatch Tool
      Response   (app/tools.py)
           ↓        ↓
           └───┬────┘
               ↓
        Return Result
               ↓
        Generate Response
               ↓
      Send back to Browser
               ↓
       Display in UI ✅
```

---

## Project Structure

```
VoiceOps-AI/
├── frontend/
│   ├── index.html              # Main UI (HTML + CSS + JavaScript)
│   └── index-old.html          # Backup of old UI
│
├── app/
│   ├── __init__.py             # Package initialization
│   ├── server.py               # FastAPI main application
│   ├── tools.py                # Backend tool functions
│   └── persona.py              # AI system instructions
│
├── docs/
│   └── ARCHITECTURE.md         # Architecture documentation
│
├── tests/
│   ├── test_server.py          # FastAPI tests
│   └── test_tools.py           # Tool function tests
│
├── .env.example                # Environment variables template
├── .env                        # Your local environment (DO NOT COMMIT)
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose (dev)
├── docker-compose.safe.yaml    # Docker Compose (safe mode)
├── README.md                   # Project overview
├── DEVELOPER_GUIDE.md          # This file
└── .gitignore                  # Git ignore rules
```

### Key Files Explained

#### `app/server.py`
- **Purpose:** Main FastAPI application
- **Handles:** WebSocket connections, routing, session management
- **Key Functions:**
  - `health()` - Health check endpoint
  - `voice_socket()` - WebSocket handler for voice chat

#### `app/tools.py`
- **Purpose:** System information gathering tools
- **Contains:** Tool declarations and implementations
- **Key Functions:**
  - `cpu_usage()` - CPU information
  - `memory_usage()` - RAM information
  - `disk_usage()` - Disk space information
  - Plus 3 more tools

#### `app/persona.py`
- **Purpose:** AI assistant personality/instructions
- **Contains:** System prompt for Gemini API
- **Customization:** Edit to change assistant behavior

#### `frontend/index.html`
- **Purpose:** Complete frontend UI
- **Contains:** HTML structure, CSS styling, JavaScript logic
- **Size:** ~25.5 KB (self-contained)
- **No dependencies:** Vanilla HTML/CSS/JS

---

## How to Add New Features

### Feature Development Workflow

```
1. Plan Feature
   └─ Identify what needs to change
   └─ Update architecture diagram if needed

2. Add Backend Tool (if needed)
   └─ Create function in app/tools.py
   └─ Add tool declaration
   └─ Test tool independently

3. Update Server
   └─ Modify app/server.py if needed
   └─ Add new endpoints if necessary

4. Update Frontend
   └─ Modify frontend/index.html
   └─ Add UI elements
   └─ Add JavaScript handlers

5. Test
   └─ Run pytest for backend
   └─ Manual testing in browser
   └─ Check console for errors

6. Document
   └─ Update README.md
   └─ Add comments to code
   └─ Update ARCHITECTURE.md
```

### Example: Adding Real-Time Container Checking

**Goal:** Add a feature to monitor running Docker containers in real-time

#### Step 1: Plan the Feature
```
What it does:
- Checks Docker containers every X seconds
- Shows status updates in chat
- Alerts if container stops

Components needed:
- Backend: Real-time polling function
- Frontend: Status display UI
- API: WebSocket message for updates
```

#### Step 2: Create Backend Tool

**Edit `app/tools.py` - Add new tool:**

```python
# Add to TOOL_DECLARATIONS list
{
    "name": "monitor_docker_containers",
    "description": "Monitor running Docker containers in real-time.",
    "parameters": {
        "type": "object",
        "properties": {
            "interval": {
                "type": "integer",
                "description": "Check interval in seconds (default 5)"
            },
            "duration": {
                "type": "integer",
                "description": "Total monitoring duration in seconds (default 60)"
            }
        }
    }
}

# Add function implementation
def docker_container_monitoring(interval: int = 5, duration: int = 60) -> Tuple:
    """
    Monitor Docker containers in real-time.
    
    Args:
        interval: Seconds between checks (default: 5)
        duration: Total duration to monitor (default: 60)
    
    Returns:
        Tuple of (event_dict, result_dict)
    """
    import time
    import docker
    
    try:
        client = docker.from_env()
        start_time = time.time()
        updates = []
        
        while (time.time() - start_time) < duration:
            containers = client.containers.list()
            current_status = {
                "timestamp": time.time(),
                "total_containers": len(containers),
                "containers": [
                    {
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else "unknown"
                    }
                    for c in containers
                ]
            }
            updates.append(current_status)
            time.sleep(interval)
        
        return (
            _event(
                "monitor_docker_containers",
                "Docker Monitoring",
                f"Monitored {len(updates)} check cycles",
                "Docker API calls",
                ok=True
            ),
            {"updates": updates, "cycles": len(updates)}
        )
    
    except Exception as e:
        return (
            _event(
                "monitor_docker_containers",
                "Docker Monitoring",
                f"Error: {str(e)}",
                "Docker API",
                ok=False
            ),
            {"error": str(e)}
        )
```

#### Step 3: Update Tool Dispatcher

**In `app/tools.py` - Update `dispatch_tool()` function:**

```python
def dispatch_tool(name: str, args: Dict[str, Any]) -> Tuple[Dict, Dict]:
    """Dispatch tool calls to appropriate handlers."""
    
    if name == "monitor_docker_containers":
        interval = args.get("interval", 5)
        duration = args.get("duration", 60)
        return docker_container_monitoring(interval, duration)
    
    # ... existing tools ...
```

#### Step 4: Test Backend Tool

**Create test file `tests/test_docker_monitoring.py`:**

```python
import pytest
from app.tools import docker_container_monitoring

def test_docker_monitoring():
    """Test Docker container monitoring."""
    event, result = docker_container_monitoring(interval=1, duration=3)
    
    assert event["name"] == "monitor_docker_containers"
    assert "updates" in result
    assert result["cycles"] > 0
```

**Run test:**
```bash
pytest tests/test_docker_monitoring.py -v
```

#### Step 5: Update Frontend UI

**Edit `frontend/index.html` - Add monitoring display:**

```javascript
// In the handleToolResult function, add:
if (data.name === "monitor_docker_containers") {
    const monitoringDiv = document.createElement("div");
    monitoringDiv.className = "tool-result monitoring";
    
    let updateHtml = data.details.updates.map((update, idx) => `
        <div class="monitoring-update">
            <strong>Cycle ${idx + 1}:</strong>
            <div class="container-list">
                ${update.containers.map(c => `
                    <div class="container-item" data-status="${c.status}">
                        <span class="status-badge ${c.status}">${c.status}</span>
                        <span class="container-name">${c.name}</span>
                        <span class="container-image">${c.image}</span>
                    </div>
                `).join("")}
            </div>
        </div>
    `).join("");
    
    monitoringDiv.innerHTML = updateHtml;
    messagesContainer.appendChild(monitoringDiv);
}
```

**Add CSS styling:**

```css
.monitoring-update {
    background: var(--bg-tertiary);
    padding: var(--spacing-md);
    margin: var(--spacing-md) 0;
    border-radius: var(--radius-md);
}

.container-item[data-status="running"] {
    border-left: 4px solid var(--accent-green);
}

.container-item[data-status="exited"] {
    border-left: 4px solid var(--accent-red);
}
```

#### Step 6: Test in Browser

1. Run server: `python -m uvicorn app.server:app --reload`
2. Open: `http://localhost:8000`
3. Type: "Monitor my Docker containers"
4. See real-time updates in chat!

#### Step 7: Document

**Update README.md:**
```markdown
## Features

### Real-Time Container Monitoring
Monitor running Docker containers with real-time status updates.
- Configurable check interval
- Shows container name, status, and image
- Color-coded status indicators
```

---

## Adding New Tools

### Complete Tool Development Guide

### Template: New Tool Structure

```python
# In app/tools.py

# 1. Add tool declaration
TOOL_DECLARATIONS = [
    # ... existing tools ...
    {
        "name": "my_new_tool",
        "description": "What this tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter 1"
                },
                "param2": {
                    "type": "integer",
                    "description": "Parameter 2"
                }
            },
            "required": ["param1"]
        }
    }
]

# 2. Implement function
def my_new_tool(param1: str, param2: int = 10) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Tool implementation.
    
    Args:
        param1: First parameter
        param2: Second parameter
    
    Returns:
        Tuple of (event_dict, result_dict)
    """
    try:
        # Your tool logic here
        result_data = {
            "value": param1,
            "count": param2
        }
        
        return (
            _event(
                "my_new_tool",
                "My Tool Title",
                "Tool executed successfully",
                "Implementation details",
                details="Additional info",
                ok=True
            ),
            result_data
        )
    
    except Exception as e:
        return (
            _event(
                "my_new_tool",
                "My Tool Title",
                f"Error: {str(e)}",
                "Implementation details",
                ok=False
            ),
            {"error": str(e)}
        )

# 3. Add to dispatcher
def dispatch_tool(name: str, args: Dict[str, Any]) -> Tuple[Dict, Dict]:
    if name == "my_new_tool":
        return my_new_tool(
            param1=args.get("param1"),
            param2=args.get("param2", 10)
        )
    # ... rest of tools ...
```

### Best Practices for Tool Development

1. **Always handle errors gracefully**
   ```python
   try:
       # your code
   except Exception as e:
       return (_event(..., ok=False), {"error": str(e)})
   ```

2. **Return consistent format**
   ```python
   return (
       _event(name, title, summary, command, details, ok),
       result_dict
   )
   ```

3. **Use read-only operations**
   - Don't modify system state
   - Don't execute arbitrary commands
   - Only gather information

4. **Document parameters**
   ```python
   def tool_name(
       param1: str,  # What it does
       param2: int = 5  # Default value explanation
   ) -> Tuple:
   ```

5. **Test before integration**
   ```bash
   pytest tests/test_your_tool.py -v
   ```

---

## Frontend Integration

### How Frontend & Backend Communicate

```
Browser (Frontend)
   ↓
HTML/CSS/JavaScript
   ├─ Captures user input (text/voice)
   ├─ Sends via WebSocket
   └─ Receives responses
   ↓
WebSocket Protocol
   ├─ Message Types:
   │  ├─ transcript (user/assistant text)
   │  ├─ tool_result (tool execution result)
   │  ├─ interrupted (user interrupted)
   │  └─ error (system error)
   ↓
FastAPI Backend
   ├─ Receives WebSocket messages
   ├─ Processes with Gemini API
   ├─ Dispatches tools if needed
   └─ Sends response back
   ↓
Frontend Display
   ├─ Shows messages in bubbles
   ├─ Displays tool results
   └─ Plays voice responses ✅
```

### WebSocket Message Formats

**User Sends Text:**
```json
{
  "type": "user_input",
  "text": "What's my CPU usage?"
}
```

**Backend Sends Transcript:**
```json
{
  "type": "transcript",
  "role": "user",
  "text": "What's my CPU usage?"
}
```

**Backend Sends Tool Result:**
```json
{
  "type": "tool_result",
  "name": "check_cpu_usage",
  "title": "CPU Usage",
  "summary": "CPU usage is 45%",
  "ok": true,
  "details": "Read-only metric"
}
```

**Backend Sends Audio:**
```
Raw binary PCM audio data
(type: bytes, not JSON)
```

### Adding UI Elements

**Example: Add new status indicator**

```html
<!-- In frontend/index.html -->

<!-- Add to header -->
<div class="status-indicators">
  <span class="indicator cpu-indicator">
    <span class="status-dot"></span>
    CPU: <span class="cpu-value">0%</span>
  </span>
  <span class="indicator memory-indicator">
    <span class="status-dot"></span>
    Memory: <span class="memory-value">0%</span>
  </span>
</div>

<!-- Add CSS -->
<style>
.status-indicators {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 12px;
  color: var(--text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-green);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

<!-- Add JavaScript -->
<script>
// Update indicators periodically
setInterval(() => {
  fetch('/api/status')
    .then(r => r.json())
    .then(data => {
      document.querySelector('.cpu-value').textContent = 
        Math.round(data.cpu) + '%';
      document.querySelector('.memory-value').textContent = 
        Math.round(data.memory) + '%';
    });
}, 5000);
</script>
```

---

## Logging & Debugging

### Enable Debug Logging

**Edit `app/server.py`:**
```python
import logging

# Add at top
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### View Logs

**While running:**
```bash
# See logs in terminal where app is running
# Look for DEBUG level messages

# Or tail log file
tail -f app.log  # Mac/Linux
Get-Content app.log -Tail 50 -Wait  # Windows
```

### Browser Console Debugging

1. Open browser DevTools: **F12**
2. Go to **Console** tab
3. See JavaScript errors
4. Run JavaScript in console:

```javascript
// Check WebSocket connection
console.log(ws);  // Should show open WebSocket

// Log all messages
ws.addEventListener('message', (event) => {
  console.log('Message received:', event.data);
});

// Send test message
ws.send('test');
```

### Python Debugging

**Using pdb (Python Debugger):**

```python
# In app/tools.py, add breakpoint
def cpu_usage():
    breakpoint()  # Execution pauses here
    # Now you can inspect variables in terminal
```

**Run with debugger:**
```bash
python -m pdb -m uvicorn app.server:app
```

**Common debugger commands:**
- `l` - List code
- `n` - Next line
- `s` - Step into function
- `c` - Continue execution
- `p variable` - Print variable
- `pp variable` - Pretty print

---

## Troubleshooting

### Common Issues & Solutions

#### "Module not found" error
```
Error: ModuleNotFoundError: No module named 'google'
Solution: pip install -r requirements.txt
```

#### "API key not found"
```
Error: InvalidArgument: API key not provided
Solution: 
1. Create .env file
2. Add: GOOGLE_API_KEY=your_key
3. Restart server
```

#### WebSocket connection fails
```
Error: WebSocket connection failed
Solutions:
1. Check if server is running: http://localhost:8000/health
2. Try different port: python -m uvicorn app.server:app --port 8001
3. Check firewall settings
4. Try different browser
```

#### Port already in use
```
Error: Address already in use
Solutions:
1. Find process using port: netstat -ano | findstr :8000 (Windows)
2. Kill process: taskkill /PID <PID> /F (Windows)
3. Use different port: python -m uvicorn app.server:app --port 8001
```

#### Tool returns no data
```
Error: Tool executed but returned empty result
Solutions:
1. Check tool logs: Look in terminal/app.log
2. Run tool independently: python -c "from app.tools import cpu_usage; print(cpu_usage())"
3. Check OS compatibility:
   - Linux: /proc files must exist
   - Windows: WMI must be accessible
   - macOS: system calls must work
```

---

## Deployment

### Docker Deployment

**Build Docker image:**
```bash
docker build -t voiceops-ai:latest .
```

**Run container:**
```bash
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your_key \
  voiceops-ai:latest
```

**Docker Compose:**
```bash
# Development with Docker socket
docker compose up

# Production safe mode (no Docker access)
docker compose -f compose.safe.yaml up
```

### Production Considerations

1. **Environment Variables**
   - Use secrets management system
   - Never commit .env to git
   - Use environment-specific configs

2. **Logging**
   - Log to file, not just console
   - Rotate logs periodically
   - Monitor for errors

3. **Performance**
   - Run multiple workers: `uvicorn app.server:app --workers 4`
   - Use reverse proxy (Nginx)
   - Add caching where appropriate

4. **Security**
   - Use HTTPS in production
   - Restrict CORS origins
   - Validate all inputs
   - Run as non-root user

5. **Monitoring**
   - Track response times
   - Monitor error rates
   - Alert on issues
   - Track API usage

---

## Best Practices

### Code Style
```python
# ✓ Good
def check_system_status(timeout: int = 30) -> Dict:
    """Check system status with timeout."""
    try:
        # implementation
        return {"status": "ok"}
    except Exception as e:
        # Handle error properly
        return {"status": "error", "message": str(e)}

# ✗ Bad
def check_sys_status(t=30):
    # Does something
    return something
```

### Documentation
```python
# ✓ Good
def cpu_usage() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Get current CPU usage.
    
    Returns:
        Tuple of (event_dict, result_dict)
        - event_dict: Metadata about the tool call
        - result_dict: Actual CPU usage data
    
    Raises:
        RuntimeError: If CPU data cannot be read
    """

# ✗ Bad
def cpu_usage():
    # get cpu
    return something
```

### Error Handling
```python
# ✓ Good
try:
    result = get_data()
except FileNotFoundError:
    logger.error("Data file not found")
    return {"error": "Data file not found"}
except Exception as e:
    logger.exception("Unexpected error")
    return {"error": str(e)}

# ✗ Bad
try:
    result = get_data()
except:
    pass
```

---

## Next Steps for New Developers

1. **Read** `ARCHITECTURE.md` for system design
2. **Run** the app locally following Setup guide
3. **Explore** each file and understand its role
4. **Modify** a tool to understand the flow
5. **Add** a simple new tool
6. **Test** your changes
7. **Document** what you learned

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini Live API](https://ai.google.dev/api/rest)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Docker Documentation](https://docs.docker.com/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

**Happy coding! 🚀**

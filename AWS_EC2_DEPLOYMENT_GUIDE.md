# 🚀 VoiceOps AI - AWS EC2 Ubuntu Deployment Guide

**Complete step-by-step guide to deploy VoiceOps AI on AWS EC2 Ubuntu instance**

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step 1: Create EC2 Instance](#step-1-create-ec2-instance)
3. [Step 2: Configure Security Group](#step-2-configure-security-group)
4. [Step 3: Connect to Instance](#step-3-connect-to-instance)
5. [Step 4: Install Dependencies](#step-4-install-dependencies)
6. [Step 5: Install UV Package Manager](#step-5-install-uv-package-manager)
7. [Step 6: Clone & Setup Project](#step-6-clone--setup-project)
8. [Step 7: Configure Environment](#step-7-configure-environment)
9. [Step 8: Run Application](#step-8-run-application)
10. [Step 9: SSH Tunneling from VS Code](#step-9-ssh-tunneling-from-vs-code)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

```
✓ AWS Account with appropriate permissions
✓ EC2 service access
✓ SSH key pair ready (or will create new one)
✓ VS Code installed (for local development)
✓ Google Gemini API key ready
✓ Your project repository accessible
```

---

## Step 1: Create EC2 Instance

### 1.1: Navigate to AWS EC2 Console

1. Open: https://console.aws.amazon.com/ec2/
2. Click: **Instances** (left sidebar)
3. Click: **Launch Instances** (blue button)

### 1.2: Select Ubuntu Image

1. Search: "ubuntu" in AMI search
2. Select: **Ubuntu Server 24.04 LTS** (latest version)
   - Architecture: 64-bit (x86)
   - Root device type: EBS
3. Click: **Select**

### 1.3: Choose Instance Type

1. Instance Type: **t2.medium**
   ```
   ✓ 1 vCPU
   ✓ 4 GB RAM
   ✓ Good for small-medium applications
   ✓ Cost-effective ($0.0464/hour)
   ```

2. Click: **Next: Configure Instance Details**

### 1.4: Configure Instance

1. Number of instances: **1**
2. Network: **Default VPC** (or your VPC)
3. Auto-assign Public IP: **Enable**
4. Leave others as default
5. Click: **Next: Add Storage**

### 1.5: Add Storage

1. Size: **25 GB** (default is usually 8-10 GB)
2. Volume type: **gp3** (General Purpose SSD)
3. Delete on termination: **Yes** (checked)
4. Click: **Next: Add Tags**

### 1.6: Add Tags (Optional)

Add tags to identify your instance:

```
Key: Name
Value: voiceops-ai-prod

Key: Environment
Value: Production

Key: Project
Value: VoiceOps-AI
```

Click: **Next: Configure Security Group**

### 1.7: Security Group Summary

Configure ports (see Step 2 for details):

```
Port 22   - SSH (for remote access)
Port 80   - HTTP (web traffic)
Port 443  - HTTPS (secure web traffic)
Port 8000 - Application (VoiceOps AI)
```

Click: **Review and Launch**

### 1.8: Review and Launch

1. Review all settings
2. Click: **Launch**
3. Choose key pair:
   - **Create new key pair** (if you don't have one)
   - Name: `voiceops-ai-key` (or your preference)
   - Type: **RSA**
   - Format: **.pem**
4. Click: **Create Key Pair**
5. Click: **Launch Instances**

**✅ Instance launching... (Wait 2-3 minutes)**

---

## Step 2: Configure Security Group

### 2.1: Wait for Instance to Be Running

1. Go to: **Instances** page
2. Wait until **Instance State** shows "Running" (green)
3. Instance has a **Public IPv4 address** assigned

### 2.2: Modify Security Group

1. Click on your instance
2. Go to: **Security** tab
3. Click on Security Group name (usually `launch-wizard-X`)

### 2.3: Edit Inbound Rules

1. Click: **Edit inbound rules**
2. Add these rules:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | 0.0.0.0/0 | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure traffic |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | VoiceOps AI app |

**Add each rule:**
1. Click: **Add rule**
2. Select Type (SSH, HTTP, etc.)
3. Leave Protocol as TCP
4. Enter Port
5. Source: 0.0.0.0/0 (anywhere - for testing only)
6. Add description
7. Click: **Save rules**

### 2.4: Outbound Rules

Leave default (allow all outbound traffic):

```
All traffic | All | All | 0.0.0.0/0
::/0
```

**✅ Security Group Configured**

---

## Step 3: Connect to Instance

### 3.1: Locate Key Pair File

The `.pem` file you downloaded contains your private key.

**Location:**
- Windows: Usually in `Downloads` folder
- Mac/Linux: Usually in `~/.ssh/` or `Downloads`

### 3.2: Save Key to Safe Location

**Windows:**
```
Create folder: C:\Users\YourUsername\.ssh
Move file: voiceops-ai-key.pem into this folder
```

**Mac/Linux:**
```bash
mv ~/Downloads/voiceops-ai-key.pem ~/.ssh/
chmod 400 ~/.ssh/voiceops-ai-key.pem
```

### 3.3: Get Instance Public IP

1. Go to: **Instances** page
2. Find your instance
3. Copy: **Public IPv4 address** (looks like: `54.123.45.67`)

### 3.4: Connect via Terminal

**Windows (PowerShell or Git Bash):**
```bash
# Navigate to .ssh folder
cd C:\Users\YourUsername\.ssh

# Connect to instance
ssh -i voiceops-ai-key.pem ubuntu@YOUR_PUBLIC_IP
# Example:
ssh -i voiceops-ai-key.pem ubuntu@54.123.45.67
```

**Mac/Linux:**
```bash
ssh -i ~/.ssh/voiceops-ai-key.pem ubuntu@YOUR_PUBLIC_IP
# Example:
ssh -i ~/.ssh/voiceops-ai-key.pem ubuntu@54.123.45.67
```

**Expected Output:**
```
The authenticity of host '54.123.45.67 (54.123.45.67)' can't be established.
ED25519 key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

ubuntu@ip-172-31-xx-xx:~$
```

Type: `yes` and press Enter

**✅ Connected to EC2 Instance!**

---

## Step 4: Install Dependencies

### 4.1: Update Package Manager

```bash
sudo apt update
```

Expected output:
```
Hit:1 http://archive.ubuntu.com/ubuntu focal InRelease
Get:2 http://archive.ubuntu.com/ubuntu focal-updates InRelease
...
Reading package lists... Done
```

### 4.2: Install Python and Tools

```bash
sudo apt install -y python3 python3-venv python3-pip curl git
```

What this installs:
- `python3` - Python interpreter
- `python3-venv` - Virtual environment support
- `python3-pip` - Package manager
- `curl` - Download tool
- `git` - Version control (for cloning repository)

Expected: `Processing triggers... Done`

### 4.3: Verify Installation

```bash
python3 --version
pip3 --version
curl --version
git --version
```

**Expected Output:**
```
Python 3.12.x
pip 23.x.x
curl 7.81.x
git 2.34.x
```

**✅ Dependencies Installed**

---

## Step 5: Install UV Package Manager

UV is a faster alternative to pip for managing Python packages.

### 5.1: Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This downloads and installs UV.

**Expected Output:**
```
info: downloading uv
info: installing to /home/ubuntu/.cargo/bin/uv
```

### 5.2: Add UV to PATH

```bash
export PATH="/home/ubuntu/.local/bin:$PATH"
```

Verify it's in PATH:
```bash
uv --version
```

**Expected Output:**
```
uv 0.x.x
```

### 5.3: Make PATH Permanent

This ensures UV stays in PATH after logout/login:

```bash
echo 'export PATH="/home/ubuntu/.local/bin:$PATH"' >> ~/.bashrc
```

### 5.4: Reload Bashrc

```bash
source ~/.bashrc
```

Verify:
```bash
uv --version
```

**✅ UV Installed and Configured**

---

## Step 6: Clone & Setup Project

### 6.1: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone the project
git clone https://github.com/anikethulule/VoiceOps-AI-Real-Time-Voice-Assistant.git
```

Expected output:
```
Cloning into 'VoiceOps-AI-Real-Time-Voice-Assistant'...
remote: Enumerating objects: 123, done.
remote: Counting objects: 100% (123/123), done.
...
Receiving objects: 100% (123/123)...
```

### 6.2: Navigate to Project

```bash
cd VoiceOps-AI-Real-Time-Voice-Assistant
```

Verify files:
```bash
ls -la
```

You should see:
```
app/
frontend/
docs/
requirements.txt
.env.example
...
```

### 6.3: Create Virtual Environment with UV

```bash
uv venv .venv
```

Expected output:
```
Using CPython 3.12.x
Creating virtual environment at '.venv'
```

### 6.4: Activate Virtual Environment

```bash
source .venv/bin/activate
```

You should see `(.venv)` prefix in terminal:
```
(.venv) ubuntu@ip-172-31-xx-xx:~/VoiceOps-AI-Real-Time-Voice-Assistant$
```

**✅ Virtual Environment Created and Activated**

---

## Step 7: Configure Environment

### 7.1: Copy .env Example

```bash
cp .env.example .env
```

### 7.2: Edit .env File

```bash
nano .env
```

This opens nano text editor.

Add your Google API key:

```
GOOGLE_API_KEY=YOUR_API_KEY_HERE
LOG_LEVEL=INFO
LIVE_MODEL=gemini-3.8-live
LIVE_VOICE=Aoede
```

Replace `YOUR_API_KEY_HERE` with your actual key.

**Save file:**
1. Press: `Ctrl + O`
2. Press: `Enter`
3. Press: `Ctrl + X`

### 7.3: Verify .env

```bash
cat .env
```

You should see your configuration:
```
GOOGLE_API_KEY=AIzaSyD_...
LOG_LEVEL=INFO
LIVE_MODEL=gemini-3.8-live
LIVE_VOICE=Aoede
```

**✅ Environment Configured**

---

## Step 8: Install Dependencies & Run Application

### 8.1: Install Requirements with UV

```bash
uv sync
```

This installs all dependencies from `pyproject.toml` and/or `requirements.txt`.

Expected output:
```
Resolved 23 packages
Installed 23 packages in 15.23s
```

### 8.2: If UV Sync Fails (Fallback)

```bash
uv pip install -r requirements.txt
```

Expected output:
```
Successfully installed fastapi-0.100.x uvicorn-0.23.x google-generativeai-0.3.x...
```

### 8.3: Run the Application

```bash
uv run uvicorn app.server:app --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Started server process [1234]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**⚠️ Note:** Application is running on 127.0.0.1 (localhost), so it's only accessible from the instance itself.

**Keep this terminal open!** The application must stay running.

**✅ Application is Running**

---

## Step 9: SSH Tunneling from VS Code

Since the application runs on localhost:8000 on the EC2 instance, you need SSH tunneling to access it from your local browser.

### 9.1: Create PEM File in VS Code

1. Open VS Code
2. Create new file: `voiceops-ai-key.pem`
3. Copy contents of your downloaded `.pem` file into this file
4. Save in a safe location (e.g., `C:\Users\YourUsername\.ssh\voiceops-ai-key.pem`)

### 9.2: Change Permissions (Windows)

**Using PowerShell (Run as Admin):**

```powershell
# Navigate to .ssh folder
cd C:\Users\YourUsername\.ssh

# Check current permissions
icacls voiceops-ai-key.pem

# Remove all permissions
icacls voiceops-ai-key.pem /inheritance:r

# Give only your user full permissions
icacls voiceops-ai-key.pem /grant:r "$env:USERNAME`:F"
```

**Expected output:**
```
processed file: voiceops-ai-key.pem
Successfully processed 1 file
```

### 9.3: Change Permissions (Mac/Linux)

```bash
chmod 400 ~/.ssh/voiceops-ai-key.pem
```

Verify:
```bash
ls -l ~/.ssh/voiceops-ai-key.pem
```

Should show: `-r--------` (read-only)

### 9.4: Create SSH Tunnel

**Windows (PowerShell):**
```powershell
ssh -i ai-test.pem -L 8000:localhost:8000 ubuntu@15.206.179.233

# Example:
ssh -i C:\Users\YourUsername\.ssh\voiceops-ai-key.pem -L 8000:localhost:8000 ubuntu@54.123.45.67
```

**Mac/Linux:**
```bash
ssh -i ~/.ssh/voiceops-ai-key.pem -L 8000:localhost:8000 ubuntu@YOUR_PUBLIC_IP

# Example:
ssh -i ~/.ssh/voiceops-ai-key.pem -L 8000:localhost:8000 ubuntu@54.123.45.67
```

**What this command does:**
- `-i` - Use this identity file (private key)
- `-L 8000:localhost:8000` - Forward local port 8000 to remote localhost:8000
- Keeps tunnel open (you stay connected)

**Keep this tunnel open!** The connection must stay active.

### 9.5: Access Application from Browser

Once tunnel is established, open your browser:

```
http://localhost:8000
```

You should see the VoiceOps AI interface!

**✅ Application is Accessible**

---

## Alternative: Running Application in Background

If you want to close the SSH tunnel but keep the app running:

### Option 1: Run with Nohup

```bash
# While connected to EC2
nohup uv run uvicorn app.server:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
```

Then you can:
- Close SSH connection
- Create new SSH tunnel just for forwarding (no interactive shell)
- Application keeps running

### Option 2: Use Systemd Service

Create service file:
```bash
sudo nano /etc/systemd/system/voiceops-ai.service
```

Add:
```
[Unit]
Description=VoiceOps AI Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/VoiceOps-AI-Real-Time-Voice-Assistant
Environment="PATH=/home/ubuntu/.local/bin:/home/ubuntu/.venv/bin"
ExecStart=/home/ubuntu/.local/bin/uv run uvicorn app.server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable voiceops-ai
sudo systemctl start voiceops-ai
```

Check status:
```bash
sudo systemctl status voiceops-ai
```

---

## Troubleshooting

### "Permission denied" when connecting SSH

**Problem:** `.pem` file has wrong permissions

**Solution:**
```bash
# Windows (PowerShell Admin)
icacls voiceops-ai-key.pem /inheritance:r
icacls voiceops-ai-key.pem /grant:r "$env:USERNAME`:F"

# Mac/Linux
chmod 400 ~/.ssh/voiceops-ai-key.pem
```

---

### "Could not resolve hostname"

**Problem:** Instance public IP is incorrect

**Solution:**
1. Go to AWS Console
2. Check Instance details
3. Copy correct Public IPv4 address
4. Try connecting again

---

### "Connection refused" on localhost:8000

**Problem:** SSH tunnel not established

**Solution:**
1. Check if tunnel command is still running
2. Create new tunnel: `ssh -i key.pem -L 8000:localhost:8000 ubuntu@IP`
3. Refresh browser

---

### "GOOGLE_API_KEY not found" error

**Problem:** .env file not properly configured

**Solution:**
```bash
# Check .env file
cat .env

# If key is missing, edit again
nano .env

# Restart application after saving
# Stop: Ctrl+C
# Start: uv run uvicorn app.server:app --host 127.0.0.1 --port 8000
```

---

### "Port 8000 already in use"

**Problem:** Application already running on that port

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 PID

# Or use different port
uv run uvicorn app.server:app --host 127.0.0.1 --port 8001
```

---

## Monitoring & Logs

### View Application Logs

```bash
# If running in foreground
# (output visible directly)

# If running in background
tail -f app.log

# Real-time monitoring
tail -f app.log | grep ERROR
```

### Check System Resources

```bash
# CPU and Memory usage
top

# Disk usage
df -h

# Memory in detail
free -h
```

### Check Application Status

```bash
# If using systemd
sudo systemctl status voiceops-ai

# If running directly
ps aux | grep uvicorn
```

---

## Security Recommendations

### For Production Deployment

1. **Restrict SSH Access**
   - Change Security Group source from `0.0.0.0/0` to your IP only
   - Or use bastion host/jump server

2. **Use HTTPS**
   - Install SSL certificate (Let's Encrypt)
   - Configure reverse proxy (Nginx)
   - Forward HTTP to HTTPS

3. **Environment Variables**
   - Don't hardcode API keys
   - Use AWS Secrets Manager
   - Rotate keys regularly

4. **Monitoring**
   - Setup CloudWatch alarms
   - Monitor CPU, memory, disk
   - Setup log aggregation

5. **Backups**
   - Regular snapshots of EBS volume
   - Backup .env file securely

6. **Firewall**
   - Only expose necessary ports
   - Use AWS WAF for DDoS protection

---

## Cost Estimation

**Typical Monthly Cost:**

| Resource | Type | Cost |
|----------|------|------|
| EC2 t2.medium | On-demand | ~$33.74/month |
| EBS 25GB | Storage | ~$2.50/month |
| Data transfer | Outbound | Variable |
| **Total** | | **~$40-50/month** |

**Ways to Save:**
- Use Reserved Instances (40% discount for 1-year)
- Use Spot Instances (70% discount, interruptible)
- Stop instance when not in use
- Use AWS Free Tier (1 year free for t2.micro)

---

## Summary Checklist

- [x] Created EC2 instance (t2.medium, 25GB storage)
- [x] Configured Security Group (SSH, HTTP, HTTPS, 8000)
- [x] Connected via SSH
- [x] Installed Python, pip, curl, git
- [x] Installed UV package manager
- [x] Cloned project repository
- [x] Created virtual environment
- [x] Configured .env with API key
- [x] Installed dependencies (uv sync)
- [x] Running application (uvicorn)
- [x] SSH tunneling from local machine
- [x] Accessing application via browser

**✅ Deployment Complete!**

---

## Next Steps

1. **Monitor application** - Check logs regularly
2. **Setup backups** - EBS snapshots
3. **Configure SSL** - Let's Encrypt + Nginx
4. **Setup monitoring** - CloudWatch alarms
5. **Plan scaling** - Load balancer if needed
6. **Document deployment** - Keep runbook updated

---

**Version:** 1.0  
**Date:** 2025  
**Status:** ✅ Production Ready  
**Difficulty:** Intermediate  
**Time Required:** 20-30 minutes

**Happy Deploying! 🚀**

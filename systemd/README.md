# Systemd Deployment

This directory contains systemd unit files for deploying Ralph on Ubuntu/Debian systems.

## Files

- `ralph.service` - Oneshot service that runs the blog generation loop
- `ralph.timer` - Timer that triggers daily generation (sys-002)

## Prerequisites

1. Ubuntu 20.04+ or Debian 11+
2. Python 3.10+
3. Supabase project with required tables
4. Anthropic API key

## Installation

### 1. Create ralph user

```bash
sudo useradd -r -s /bin/false ralph
```

### 2. Deploy application

```bash
# Create application directory
sudo mkdir -p /opt/ralph
sudo chown ralph:ralph /opt/ralph

# Clone or copy application files
sudo -u ralph git clone https://github.com/your-org/ai-blog.git /opt/ralph
# Or: sudo cp -r /path/to/ai-blog/* /opt/ralph/

# Create virtual environment
cd /opt/ralph
sudo -u ralph python3 -m venv .venv
sudo -u ralph .venv/bin/pip install -r requirements.txt
```

### 3. Create environment file

```bash
# Create secure directory
sudo mkdir -p /etc/ralph
sudo chmod 700 /etc/ralph

# Create environment file
sudo tee /etc/ralph/env > /dev/null << 'EOF'
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET=sb_secret_your-service-role-key

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-your-key

# Ralph Configuration
RALPH_QUALITY_THRESHOLD=0.85
RALPH_TIMEOUT_MINUTES=30
RALPH_COST_LIMIT_CENTS=100
RALPH_JUICE_THRESHOLD=0.6
EOF

# Secure the file
sudo chmod 600 /etc/ralph/env
sudo chown root:ralph /etc/ralph/env
```

### 4. Install systemd service

```bash
# Copy service file
sudo cp /opt/ralph/systemd/ralph.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Verify service is recognized
sudo systemctl status ralph.service
```

### 5. Test manual execution

```bash
# Run once manually
sudo systemctl start ralph.service

# Check logs
sudo journalctl -u ralph.service -f

# Verify exit status
sudo systemctl status ralph.service
```

## Customization

Edit `/etc/systemd/system/ralph.service` if you need to change:

- `User/Group` - Different service account
- `WorkingDirectory` - Different install location
- `EnvironmentFile` - Different env file path
- `TimeoutStartSec` - Different timeout (default: 30 minutes)

After editing:
```bash
sudo systemctl daemon-reload
```

## Troubleshooting

### Check service status
```bash
sudo systemctl status ralph.service
```

### View logs
```bash
# Recent logs
sudo journalctl -u ralph.service -n 50

# Follow logs in real-time
sudo journalctl -u ralph.service -f

# Logs since last boot
sudo journalctl -u ralph.service -b
```

### Common issues

**Service fails immediately:**
- Check environment file exists and is readable
- Verify virtual environment has all dependencies
- Check WorkingDirectory path is correct

**Permission denied:**
- Ensure ralph user owns /opt/ralph
- Ensure /etc/ralph/env is readable by ralph group
- Check file permissions: `ls -la /opt/ralph /etc/ralph/env`

**Python module not found:**
- Verify virtual environment is activated in ExecStart path
- Check requirements.txt was installed in venv

**Timeout:**
- Increase TimeoutStartSec in service file
- Check RALPH_TIMEOUT_MINUTES in environment

## Exit Codes

- `0` - Success (published, draft, skipped, or skipped_no_juice)
- `1` - Failure (error during generation)

The service is Type=oneshot, so it will show `inactive (dead)` after completion. This is normal.

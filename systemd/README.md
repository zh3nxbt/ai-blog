# Systemd Deployment

This directory contains systemd unit files for deploying Ralph on Ubuntu/Debian systems.

## Files

- `ralph.service` - Oneshot service that runs the blog generation loop (template)
- `ralph.timer` - Timer that triggers daily generation at 2:12 PM UTC
- `ralph-refresh.service` - Oneshot service that refreshes RSS sources only
- `ralph-refresh.timer` - Timer that triggers hourly RSS refresh
- `install.sh` - Automated installation script

## Quick Install

```bash
# From the project root directory, run as root:
sudo ./systemd/install.sh

# Or specify a custom project path:
sudo ./systemd/install.sh /path/to/ai-blog
```

The install script will:
1. Create the `ralph` system user
2. Set up `/etc/ralph/env` with secure permissions
3. Install the systemd service with correct paths
4. Set proper ownership on the project directory

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
RALPH_REFRESH_LIMIT_PER_SOURCE=20
# Optional
# RALPH_REFRESH_MAX_SOURCES=25
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

### 6. Enable the timer for daily automation

```bash
# Enable timer to start on boot
sudo systemctl enable ralph.timer

# Start the timer now
sudo systemctl start ralph.timer

# Verify timer is active
sudo systemctl list-timers ralph.timer
```

The generation timer runs daily at **2:12 PM UTC (14:12)**. The service checks source "juice" first and only generates content if sources have real value.

### 7. Enable hourly RSS refresh timer

```bash
# Enable timer to start on boot
sudo systemctl enable ralph-refresh.timer

# Start the timer now
sudo systemctl start ralph-refresh.timer

# Verify timer is active
sudo systemctl list-timers ralph-refresh.timer
```

This timer refreshes RSS items every hour and **does not call Anthropic/LLM APIs**.

## Timer Details

The `ralph.timer` unit triggers `ralph.service` daily:

- **Schedule:** `*-*-* 14:12:00 UTC` (every day at 2:12 PM UTC)
- **Purpose:** Run generation shortly after hourly refresh at minute 5
- **Persistent:** If the system was off at run time, the timer runs on next boot
- **Randomized Delay:** Up to 60 seconds to avoid thundering herd

The `ralph-refresh.timer` unit triggers `ralph-refresh.service` hourly:

- **Schedule:** `*-*-* *:05:00 UTC` (every hour at minute 5)
- **Purpose:** Refresh and deduplicate RSS items only
- **LLM usage:** None

### Timer Commands

```bash
# Check timer status
sudo systemctl status ralph.timer
sudo systemctl status ralph-refresh.timer

# List when timer will next trigger
sudo systemctl list-timers ralph.timer
sudo systemctl list-timers ralph-refresh.timer

# View timer logs
sudo journalctl -u ralph.timer
sudo journalctl -u ralph-refresh.timer

# Disable daily automation
sudo systemctl stop ralph.timer
sudo systemctl disable ralph.timer
sudo systemctl stop ralph-refresh.timer
sudo systemctl disable ralph-refresh.timer
```

### Behavior

When the timer triggers:
1. `ralph.service` starts
2. Service evaluates source "juice" (are sources worth writing about?)
3. If juice score >= 0.6: generates content
4. If juice score < 0.6: skips with status `skipped_no_juice`
5. Service exits (oneshot behavior)

This prevents forced daily posts when there's no valuable content.

When the hourly refresh timer triggers:
1. `ralph-refresh.service` starts
2. Active RSS feeds are fetched and deduplicated into `blog_rss_items`
3. Source fetch timestamps are updated
4. Service exits (oneshot behavior)

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

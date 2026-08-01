#!/bin/bash
#
# Blog Systemd Installation Script
# Usage: sudo ./install.sh [project_path]
#
# If project_path is not provided, uses the parent directory of this script.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Determine project path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="${1:-$(dirname "$SCRIPT_DIR")}"

# Validate project path
if [[ ! -f "$PROJECT_PATH/blog/generate.sh" ]]; then
    log_error "Invalid project path: $PROJECT_PATH"
    log_error "Could not find blog/generate.sh"
    exit 1
fi

if [[ ! -f "$PROJECT_PATH/.env" ]]; then
    log_error "Missing .env file in $PROJECT_PATH"
    log_error "Copy .env.example to .env and configure it first"
    exit 1
fi

if [[ ! -d "$PROJECT_PATH/.venv" ]]; then
    log_error "Missing .venv directory in $PROJECT_PATH"
    log_error "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

if ! grep -Eq '^ANTHROPIC_API_KEY=.+$' "$PROJECT_PATH/.env"; then
    log_warn "ANTHROPIC_API_KEY not found in .env"
    log_warn "Headless claude -p runs will fail unless user 'blog' is logged in via 'claude auth login'"
fi

log_info "Project path: $PROJECT_PATH"

# Step 1: Create blog user if it doesn't exist
if id "blog" &>/dev/null; then
    log_info "User 'blog' already exists"
else
    # Claude CLI requires a real shell and home directory
    log_info "Creating user 'blog' with /bin/bash shell..."
    useradd -r -m -s /bin/bash blog
    log_info "User 'blog' created"
fi

# Ensure blog has a home directory for Claude CLI auth tokens
if [[ ! -d /home/blog ]]; then
    mkdir -p /home/blog
    chown blog:blog /home/blog
fi

# Step 2: Create environment directory and file
log_info "Setting up /etc/blog-backend/env..."
mkdir -p /etc/blog-backend
cp "$PROJECT_PATH/.env" /etc/blog-backend/env
chmod 600 /etc/blog-backend/env
chown root:blog /etc/blog-backend/env
chmod 750 /etc/blog-backend
log_info "Environment file installed with secure permissions"

# Step 3: Set ownership of project directory
log_info "Setting ownership of project directory..."
chown -R blog:blog "$PROJECT_PATH"
log_info "Project directory owned by blog:blog"

# Step 4: Generate and install systemd service file
log_info "Installing systemd service..."

# Create service file with correct paths
cat > /etc/systemd/system/blog-generator.service << EOF
[Unit]
Description=Blog Content Generator
Documentation=https://github.com/zh3nxbt/mas-website-blog
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot

# Run as non-root user (needs /bin/bash shell for Claude CLI)
User=blog
Group=blog

# Project location
WorkingDirectory=$PROJECT_PATH

# Load environment from secure location
EnvironmentFile=/etc/blog-backend/env

# Claude CLI needs HOME for auth tokens
Environment=HOME=/home/blog
Environment=PYTHONUNBUFFERED=1

# Execute blog generation via Claude Code CLI
ExecStart=/bin/bash $PROJECT_PATH/blog/generate.sh

# Logging to stdout/stderr (captured by journald)
StandardOutput=journal
StandardError=journal

# Timeout: 45 minutes (Claude Code may be slower than direct API)
TimeoutStartSec=2700

# Restart policy for oneshot is ignored, but set for documentation
Restart=no

[Install]
WantedBy=multi-user.target
EOF

log_info "Service file installed to /etc/systemd/system/blog-generator.service"

# Step 5: Install generation timer file
log_info "Installing generation timer..."
cat > /etc/systemd/system/blog-generator.timer << EOF
[Unit]
Description=Blog Content Generation Timer (Mon/Wed/Fri)
Documentation=https://github.com/zh3nxbt/mas-website-blog

[Timer]
# Run Mon/Wed/Fri at 2:12 PM UTC (14:12), shortly after hourly feed refresh.
OnCalendar=Mon,Wed,Fri *-*-* 14:12:00 UTC
Unit=blog-generator.service

# If the system was off when the timer should have triggered,
# run it immediately on next boot
Persistent=true

# Add some randomized delay to avoid thundering herd
RandomizedDelaySec=60

# Accuracy: how much the timer can be coalesced with other timers
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

log_info "Generation timer file installed to /etc/systemd/system/blog-generator.timer"

# Step 6: Install RSS refresh service
log_info "Installing RSS refresh service..."
cat > /etc/systemd/system/blog-refresh.service << EOF
[Unit]
Description=Blog RSS Source Refresh
Documentation=https://github.com/zh3nxbt/mas-website-blog
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=blog
Group=blog
WorkingDirectory=$PROJECT_PATH
EnvironmentFile=/etc/blog-backend/env
ExecStart=$PROJECT_PATH/.venv/bin/python -m blog.refresh_sources
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
TimeoutStartSec=900
Restart=no

[Install]
WantedBy=multi-user.target
EOF
log_info "RSS refresh service installed to /etc/systemd/system/blog-refresh.service"

# Step 7: Install RSS refresh timer
log_info "Installing RSS refresh timer..."
cat > /etc/systemd/system/blog-refresh.timer << EOF
[Unit]
Description=Hourly Blog RSS Source Refresh Timer
Documentation=https://github.com/zh3nxbt/mas-website-blog

[Timer]
OnCalendar=*-*-* *:05:00 UTC
Unit=blog-refresh.service
OnBootSec=5min
Persistent=true
RandomizedDelaySec=60
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF
log_info "RSS refresh timer installed to /etc/systemd/system/blog-refresh.timer"

# Step 8: Reload systemd
log_info "Reloading systemd daemon..."
systemctl daemon-reload

# Step 9: Verify installation
log_info "Verifying installation..."
echo ""
echo "=========================================="
echo "Installation Complete"
echo "=========================================="
echo ""
echo "Project path:    $PROJECT_PATH"
echo "Environment:     /etc/blog-backend/env"
echo "Service file:    /etc/systemd/system/blog-generator.service"
echo "Timer file:      /etc/systemd/system/blog-generator.timer"
echo "Refresh svc:     /etc/systemd/system/blog-refresh.service"
echo "Refresh timer:   /etc/systemd/system/blog-refresh.timer"
echo "Service user:    blog"
echo ""
echo "Next steps:"
echo ""
echo "  1. Test manual execution:"
echo "     systemctl start blog-generator.service"
echo ""
echo "  2. Check status:"
echo "     systemctl status blog-generator.service"
echo ""
echo "  3. View logs:"
echo "     journalctl -u blog-generator.service -f"
echo ""
echo "  4. Enable and start the timer for Mon/Wed/Fri 2 PM UTC automation:"
echo "     systemctl enable blog-generator.timer"
echo "     systemctl start blog-generator.timer"
echo ""
echo "  5. Enable and start hourly RSS refresh:"
echo "     systemctl enable blog-refresh.timer"
echo "     systemctl start blog-refresh.timer"
echo ""
echo "  6. Verify timers are active:"
echo "     systemctl list-timers blog-generator.timer"
echo "     systemctl list-timers blog-refresh.timer"
echo ""
echo "  7. Ensure Claude CLI is authenticated for the blog user:"
echo "     sudo -u blog claude --version"
echo "     (If not authenticated, run: sudo -u blog -i claude login)"
echo ""
echo "=========================================="

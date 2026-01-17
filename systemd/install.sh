#!/bin/bash
#
# Ralph Systemd Installation Script
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
if [[ ! -f "$PROJECT_PATH/ralph/ralph_loop.py" ]]; then
    log_error "Invalid project path: $PROJECT_PATH"
    log_error "Could not find ralph/ralph_loop.py"
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

log_info "Project path: $PROJECT_PATH"

# Step 1: Create ralph user if it doesn't exist
if id "ralph" &>/dev/null; then
    log_info "User 'ralph' already exists"
else
    log_info "Creating user 'ralph'..."
    useradd -r -s /bin/false ralph
    log_info "User 'ralph' created"
fi

# Step 2: Create environment directory and file
log_info "Setting up /etc/ralph/env..."
mkdir -p /etc/ralph
cp "$PROJECT_PATH/.env" /etc/ralph/env
chmod 600 /etc/ralph/env
chown root:ralph /etc/ralph/env
chmod 750 /etc/ralph
log_info "Environment file installed with secure permissions"

# Step 3: Set ownership of project directory
log_info "Setting ownership of project directory..."
chown -R ralph:ralph "$PROJECT_PATH"
log_info "Project directory owned by ralph:ralph"

# Step 4: Generate and install systemd service file
log_info "Installing systemd service..."

# Create service file with correct paths
cat > /etc/systemd/system/ralph.service << EOF
[Unit]
Description=Ralph Blog Content Generator
Documentation=https://github.com/your-org/ai-blog
After=network.target

[Service]
Type=oneshot

# Run as non-root user
User=ralph
Group=ralph

# Project location
WorkingDirectory=$PROJECT_PATH

# Load environment from secure location
EnvironmentFile=/etc/ralph/env

# Execute using virtual environment Python
ExecStart=$PROJECT_PATH/.venv/bin/python -m ralph.ralph_loop

# Logging to stdout/stderr (captured by journald)
StandardOutput=journal
StandardError=journal

# Timeout for the entire operation (30 minutes)
TimeoutStartSec=1800

# Restart policy for oneshot is ignored, but set for documentation
Restart=no

[Install]
WantedBy=multi-user.target
EOF

log_info "Service file installed to /etc/systemd/system/ralph.service"

# Step 5: Install systemd timer file
log_info "Installing systemd timer..."
cat > /etc/systemd/system/ralph.timer << EOF
[Unit]
Description=Daily Ralph Blog Content Generation Timer
Documentation=https://github.com/your-org/ai-blog

[Timer]
# Run daily at 2 PM UTC (14:00)
OnCalendar=*-*-* 14:00:00 UTC

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

log_info "Timer file installed to /etc/systemd/system/ralph.timer"

# Step 6: Reload systemd
log_info "Reloading systemd daemon..."
systemctl daemon-reload

# Step 7: Verify installation
log_info "Verifying installation..."
echo ""
echo "=========================================="
echo "Installation Complete"
echo "=========================================="
echo ""
echo "Project path:    $PROJECT_PATH"
echo "Environment:     /etc/ralph/env"
echo "Service file:    /etc/systemd/system/ralph.service"
echo "Timer file:      /etc/systemd/system/ralph.timer"
echo "Service user:    ralph"
echo ""
echo "Next steps:"
echo ""
echo "  1. Test manual execution:"
echo "     systemctl start ralph.service"
echo ""
echo "  2. Check status:"
echo "     systemctl status ralph.service"
echo ""
echo "  3. View logs:"
echo "     journalctl -u ralph.service -f"
echo ""
echo "  4. Enable and start the timer for daily 2 PM UTC automation:"
echo "     systemctl enable ralph.timer"
echo "     systemctl start ralph.timer"
echo ""
echo "  5. Verify timer is active:"
echo "     systemctl list-timers ralph.timer"
echo ""
echo "=========================================="

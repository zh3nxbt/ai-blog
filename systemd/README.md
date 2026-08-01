# systemd Deployment

This directory contains two oneshot services and their timers:

- `blog-refresh.service` runs `python -m blog.refresh_sources`.
- `blog-refresh.timer` triggers the refresh service hourly at minute 5 UTC.
- `blog-generator.service` runs `blog/generate.sh`.
- `blog-generator.timer` triggers generation Monday, Wednesday, and Friday at 14:12 UTC.

## Install

From the repository root:

```bash
sudo ./systemd/install.sh /opt/blog-backend
sudo systemctl enable --now blog-refresh.timer blog-generator.timer
```

The installer:

1. Creates the unprivileged `blog` service account.
2. copies `.env` to `/etc/blog-backend/env` with restricted permissions.
3. assigns the project directory to the service account.
4. installs the four units in `/etc/systemd/system/`.
5. reloads systemd.

## Operate

```bash
sudo systemctl start blog-refresh.service
sudo systemctl start blog-generator.service

sudo systemctl status blog-refresh.service blog-generator.service
sudo systemctl list-timers blog-refresh.timer blog-generator.timer

sudo journalctl -u blog-refresh.service -f
sudo journalctl -u blog-generator.service -f
```

Before enabling generation, verify Claude authentication for the service account:

```bash
sudo -u blog -i claude auth status
```

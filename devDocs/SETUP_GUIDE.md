# Environment and Deployment Guide

## Required configuration

Create `.env` from `.env.example` and set:

- `SUPABASE_URL`: project API URL.
- `SUPABASE_KEY`: public key for frontend-compatible operations.
- `SUPABASE_SECRET`: service-role key used by backend jobs.
- `ENVIRONMENT`: use `production` on the production server.
- `API_HOST`: bind address for FastAPI. Use `0.0.0.0` behind the server firewall or reverse proxy.
- `API_PORT`: FastAPI listening port. Default: `8000`.

For direct SQL migrations, also set `DATABASE_URL` or `SUPABASE_DB_PASSWORD`. The migration utilities can use `SUPABASE_POOLER_HOST` when a specific IPv4-compatible pooler is required.

## RSS refresh configuration

- `BLOG_REFRESH_LIMIT_PER_SOURCE`: maximum items stored per source and run. Default: `20`.
- `BLOG_REFRESH_MAX_SOURCES`: optional cap on active sources processed per run.
- `BLOG_RSS_FAILURE_THRESHOLD`: consecutive failures before a feed is disabled. Default: `5`.
- `BLOG_RSS_FETCH_RETRIES`: attempts per source and run. Default: `2`.

## Claude Code authentication

The generation runner calls `claude -p`. Authenticate the operating-system account that owns the scheduled job:

```bash
claude auth login
claude auth status
```

For unattended environments, `ANTHROPIC_API_KEY` may be supplied to the job environment instead. Keep it outside the repository.

## Local verification

```bash
python -m blog.generate_helpers --help
python -m blog.refresh_sources --help
pytest
```

Run generation only after the Supabase credentials and Claude authentication are configured:

```bash
bash blog/generate.sh
```

## Windows local operation

Run the launcher from Command Prompt or by double-clicking it:

```bat
run-ai-blog.bat
```

The default command performs two actions:

1. Validates `.env`, the virtual environment, and the FastAPI runtime.
2. Starts the FastAPI server in the foreground using `API_HOST` and `API_PORT`.

The default command does not create or change scheduled tasks. To make a
Windows machine an intentional job runner, install the schedules explicitly:

```bat
run-ai-blog.bat install-schedule
```

The refresh task runs hourly at minute `05`. The generation task wakes hourly
at minute `12`, checks UTC, and proceeds only on Monday, Wednesday, or Friday
after `14:12 UTC`. Before invoking Claude, it queries Supabase for an existing
post on the current UTC date. This preserves the Linux schedule across Toronto
daylight-saving changes. `StartWhenAvailable` catches missed triggers, and an
ignored `.runtime/last-generation-attempt-utc.txt` marker prevents repeated
Claude runs after a successful, failed, or intentionally skipped attempt.

Schedule installation is idempotent. Use these modes for maintenance:

```bat
run-ai-blog.bat check
run-ai-blog.bat install-schedule
run-ai-blog.bat refresh
run-ai-blog.bat generate
run-ai-blog.bat generate-if-due
run-ai-blog.bat server
```

Tasks are registered with the current account's interactive logon token so its
Claude authentication is available without storing a Windows password. That
account must remain logged on. Task settings allow battery operation, prevent
overlapping copies, start missed work when available, and limit refresh and
generation runs to 15 and 45 minutes respectively.

Do not install these tasks on a development workstation when the Linux
production timers are already responsible for the jobs.

## Linux deployment

On the Ubuntu production server, place the repository at
`/opt/blog-backend`. From that directory, create the environment and install
dependencies:

```bash
cd /opt/blog-backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with the production Supabase and Claude credentials, set
`ENVIRONMENT=production`, and confirm `API_HOST` and `API_PORT`. Then install
the systemd units and start the runtime:

```bash
sudo ./systemd/install.sh /opt/blog-backend
sudo systemctl enable --now blog-api.service blog-refresh.timer blog-generator.timer
```

Check status and logs:

```bash
sudo systemctl status blog-api.service
sudo systemctl list-timers blog-refresh.timer blog-generator.timer
sudo systemctl status blog-refresh.service blog-generator.service
sudo journalctl -u blog-api.service -n 100 --no-pager
sudo journalctl -u blog-refresh.service -n 100 --no-pager
sudo journalctl -u blog-generator.service -n 100 --no-pager
curl http://127.0.0.1:8000/health
```

The installer copies `.env` to `/etc/blog-backend/env` with restricted
permissions, installs the persistent FastAPI service and both job timers, and
runs everything as the dedicated `blog` user.

If `.env` does not provide `ANTHROPIC_API_KEY`, authenticate Claude after the
installer creates the service account:

```bash
sudo -u blog -i claude auth login
sudo -u blog -i claude auth status
```

Keep port `8000` behind the production firewall or reverse proxy; do not expose
the administrative API directly to the public internet.

## Security

- Never commit `.env`, API keys, database passwords, or service-role credentials.
- Keep `/etc/blog-backend/env` readable only by root and the service account.
- Run scheduled jobs as the unprivileged `blog` user.
- Rotate credentials after any suspected exposure.

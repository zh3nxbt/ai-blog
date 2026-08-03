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

## Windows production deployment

Windows is the primary production environment. Use a dedicated Windows account
and complete the entire installation while signed in as that account.

### Install the runtime

Open Command Prompt in the production checkout:

```bat
cd /d D:\path\to\mas-website-blog
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Set the production credentials, `ENVIRONMENT=production`, `API_HOST`, and
`API_PORT`. Confirm that Git Bash and the Claude CLI are on the production
account's `PATH`, then authenticate and validate everything:

```bat
claude auth login
claude auth status
run-ai-blog.bat check
```

### Install the scheduled jobs

Install the schedules explicitly:

```bat
run-ai-blog.bat install-schedule
```

The command is idempotent and creates or updates:

- `AI Blog - RSS Refresh`: hourly at minute `05`, with a 15-minute limit.
- `AI Blog - Post Generation`: checks hourly at minute `12`, with a 45-minute
  limit, and generates only Monday, Wednesday, and Friday after `14:12 UTC`.

Before generation, the task checks Supabase for an existing post on the current
UTC date. `StartWhenAvailable` catches missed triggers, overlapping copies are
blocked, and `.runtime/last-generation-attempt-utc.txt` prevents repeated
Claude runs after an attempted scheduled date.

The jobs use the production account's interactive logon token so its Claude
authentication is available without storing a Windows password. Keep that
account logged on. Task actions use hidden PowerShell windows so scheduled runs
do not interrupt the production desktop.

### Start and verify the API

```bat
run-ai-blog.bat server
```

Keep the server Command Prompt open. Verify from another terminal:

```bat
curl.exe http://127.0.0.1:8000/health
schtasks /Query /TN "AI Blog - RSS Refresh" /V /FO LIST
schtasks /Query /TN "AI Blog - Post Generation" /V /FO LIST
```

After rebooting Windows, sign in to the production account and start the server
again. The API is not currently installed as a Windows service. Running
`run-ai-blog.bat` without an argument also starts only the server and never
installs schedules.

### Operations

```bat
run-ai-blog.bat check
run-ai-blog.bat refresh
run-ai-blog.bat generate
run-ai-blog.bat generate-if-due
run-ai-blog.bat server
```

Pause or resume production automation from PowerShell:

```powershell
Disable-ScheduledTask -TaskName "AI Blog - RSS Refresh"
Disable-ScheduledTask -TaskName "AI Blog - Post Generation"

Enable-ScheduledTask -TaskName "AI Blog - RSS Refresh"
Enable-ScheduledTask -TaskName "AI Blog - Post Generation"
```

Rerun `run-ai-blog.bat install-schedule` after changing the launcher so the
registered task actions and settings are refreshed.

## Development workstation

Use `run-ai-blog.bat` to start the local API. Do not run `install-schedule` on a
development machine; the production Windows host owns RSS refresh and post
generation.

## Optional Linux/systemd deployment

On an optional Ubuntu server, place the repository at
`/opt/blog-backend`. From that directory, create the environment and install
dependencies:

```bash
cd /opt/blog-backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with the server's Supabase and Claude credentials, set
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

Keep port `8000` behind the server firewall or reverse proxy; do not expose
the administrative API directly to the public internet.

## Security

- Never commit `.env`, API keys, database passwords, or service-role credentials.
- Restrict the Windows `.env` file to the production account and administrators.
- Run the API and scheduled jobs under the dedicated production account.
- Keep `/etc/blog-backend/env` restricted when using the optional Linux deployment.
- Rotate credentials after any suspected exposure.

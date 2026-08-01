# Environment and Deployment Guide

## Required configuration

Create `.env` from `.env.example` and set:

- `SUPABASE_URL`: project API URL.
- `SUPABASE_KEY`: public key for frontend-compatible operations.
- `SUPABASE_SECRET`: service-role key used by backend jobs.

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

## Windows deployment

Run the launcher from Command Prompt or by double-clicking it:

```bat
run-ai-blog.bat
```

The default command performs three actions in order:

1. Validates `.env`, the virtual environment, Git Bash, Claude Code, and the
   Windows ScheduledTasks module.
2. Creates or updates `AI Blog - RSS Refresh` and
   `AI Blog - Post Generation` for the current Windows user.
3. Starts the FastAPI server in the foreground using `API_HOST` and `API_PORT`.

The refresh task runs hourly at minute `05`. The generation task wakes hourly
at minute `12`, checks UTC, and proceeds only on Monday, Wednesday, or Friday
after `14:12 UTC`. Before invoking Claude, it queries Supabase for an existing
post on the current UTC date. This preserves the Linux schedule across Toronto
daylight-saving changes. `StartWhenAvailable` catches missed triggers, and an
ignored `.runtime/last-generation-attempt-utc.txt` marker prevents repeated
Claude runs after a successful, failed, or intentionally skipped attempt.

The launcher is idempotent. Use the narrower modes for maintenance:

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

## Linux deployment

Install the systemd units from the repository root:

```bash
sudo ./systemd/install.sh /opt/blog-backend
sudo systemctl enable --now blog-refresh.timer blog-generator.timer
```

Check status and logs:

```bash
sudo systemctl list-timers blog-refresh.timer blog-generator.timer
sudo systemctl status blog-refresh.service blog-generator.service
sudo journalctl -u blog-refresh.service -n 100 --no-pager
sudo journalctl -u blog-generator.service -n 100 --no-pager
```

The installer copies `.env` to `/etc/blog-backend/env` with restricted permissions and runs both jobs as the dedicated `blog` user.

## Security

- Never commit `.env`, API keys, database passwords, or service-role credentials.
- Keep `/etc/blog-backend/env` readable only by root and the service account.
- Run scheduled jobs as the unprivileged `blog` user.
- Rotate credentials after any suspected exposure.

# AI Blog Backend

Backend service that collects stable manufacturing sources, generates blog posts for MAS Precision Parts, validates them, and stores them in Supabase.

## Runtime

Production runs a FastAPI service plus two independent jobs:

1. `api.main:app` provides health and administrative HTTP endpoints.
2. `python -m blog.refresh_sources` fetches active RSS feeds and stores new, deduplicated source items.
3. `blog/generate.sh` runs the Claude Code CLI with `blog/prompts/generate.md`, validates the result, and saves one post.

Generation is idempotent. If a post already exists for the current UTC day, the job records a skipped outcome and stops.

## Requirements

- Python 3.11 or newer
- A Supabase project with the repository migrations applied
- Claude Code CLI for post generation
- Git Bash on Windows, or Bash on Linux

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
```

Linux or Git Bash:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure:

```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-public-key
SUPABASE_SECRET=your-service-role-key

BLOG_REFRESH_LIMIT_PER_SOURCE=20
BLOG_RSS_FAILURE_THRESHOLD=5
BLOG_RSS_FETCH_RETRIES=2

ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
```

`SUPABASE_SECRET` is required by backend jobs. Never commit `.env` or service-role credentials.

For unattended Claude Code execution, authenticate the scheduled-task user with `claude auth login` or provide `ANTHROPIC_API_KEY` in that user's environment.

## Local commands

Refresh RSS sources:

```bash
python -m blog.refresh_sources
```

Inspect the generation helpers:

```bash
python -m blog.generate_helpers --help
python -m blog.generate_helpers check-today
python -m blog.generate_helpers fetch-sources --rss-limit 2 --topic-limit 1
```

Run one generation job:

```bash
bash blog/generate.sh
```

Run the API:

```bash
uvicorn api.main:app --reload
```

Run tests:

```bash
pytest
```

## Production deployment

Linux deployment units are in `systemd/`:

- `blog-api.service` keeps the FastAPI application running.
- `blog-refresh.timer` refreshes RSS sources hourly.
- `blog-generator.timer` starts generation on Monday, Wednesday, and Friday.

On the Ubuntu production server, place the repository at `/opt/blog-backend`,
create `.env` with the production values described above, then install and
start the runtime:

```bash
cd /opt/blog-backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo ./systemd/install.sh /opt/blog-backend
sudo systemctl enable --now blog-api.service blog-refresh.timer blog-generator.timer
curl http://127.0.0.1:8000/health
```

The installer creates the unprivileged `blog` account, copies `.env` to
`/etc/blog-backend/env`, installs the API service and job timers, and reloads
systemd. See `systemd/README.md` for status, log, and manual-run commands.
Expose the API port only through the production firewall or reverse proxy.

## Windows local operation

Use the repository launcher to start only the FastAPI server in the foreground:

```bat
run-ai-blog.bat
```

The default command does not create or change scheduled tasks. Install local
Windows automation only when this machine is intentionally acting as the job
runner:

```bat
run-ai-blog.bat install-schedule
```

The Windows schedule mirrors the Linux timers:

- `AI Blog - RSS Refresh` runs hourly at minute `05`.
- `AI Blog - Post Generation` evaluates the schedule hourly at minute `12`,
  then generates only on Monday, Wednesday, and Friday after `14:12 UTC`.

The UTC gate keeps the generation time correct through daylight-saving changes.
It checks for an existing post before starting Claude. Task Scheduler catches
up after the computer was unavailable, while an ignored `.runtime` marker
limits generation to one attempt per scheduled UTC date.

Useful launcher modes:

```bat
run-ai-blog.bat check
run-ai-blog.bat install-schedule
run-ai-blog.bat refresh
run-ai-blog.bat generate
run-ai-blog.bat server
```

The scheduled tasks use the current Windows account and run while that account
is logged on. Authenticate Claude Code under the same account. Do not install
these tasks on a development workstation when the Linux production timers are
already enabled.

## Project layout

```text
api/                  FastAPI health and administrative endpoints
blog/                 Generation runner, prompt, helpers, and RSS refresh entrypoint
migrations/           Supabase schema and seed migrations
services/             RSS, topic, validation, and Supabase services
skills/               Writing-quality instructions used during generation
systemd/              Linux services, timers, and installer
tests/                 Maintained automated tests
utils/                 Shared environment helpers
```

## Reliability rules

- Use RSS, vendor feeds, standards bodies, government sources, and the evergreen topic bank.
- Do not scrape restricted or fragile platforms.
- Summarize sources and preserve their URLs.
- Validate content before persistence.
- Log every run outcome to `blog_agent_activity`.
- Fail with a non-zero exit code when generation or ingestion cannot complete safely.

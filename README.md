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

## Windows production deployment

Windows is the primary production target. Use a dedicated Windows account for
the blog runtime, and run every setup command while signed in as that account.
The same account must own the Claude login and the scheduled tasks.

### 1. Install and configure

Open Command Prompt in the production checkout:

```bat
cd /d D:\path\to\mas-website-blog
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Set the production Supabase credentials, `ENVIRONMENT=production`,
`API_HOST`, and `API_PORT`. Keep `.env` restricted to the production account
and administrators.

Authenticate and verify Claude under that same Windows account:

```bat
claude auth login
claude auth status
run-ai-blog.bat check
```

### 2. Install production schedules

Scheduling is deliberately opt-in so a development checkout cannot become a
job runner merely by starting the API:

```bat
run-ai-blog.bat install-schedule
```

This creates or updates:

- `AI Blog - RSS Refresh`, which runs hourly at minute `05`.
- `AI Blog - Post Generation`, which checks hourly at minute `12` and generates
  only on Monday, Wednesday, and Friday after `14:12 UTC`.

The jobs use the current account's interactive logon token so Claude
authentication is available without storing the Windows password. Keep that
account logged on. They launch in hidden PowerShell windows, so hourly jobs do
not interrupt the production desktop. `StartWhenAvailable` catches missed runs,
overlapping copies are blocked, and `.runtime/last-generation-attempt-utc.txt`
limits generation to one attempt per scheduled UTC date.

### 3. Start and verify the API

Start FastAPI in the foreground:

```bat
run-ai-blog.bat server
```

Keep that Command Prompt open. From another terminal, verify the API and tasks:

```bat
curl.exe http://127.0.0.1:8000/health
schtasks /Query /TN "AI Blog - RSS Refresh" /V /FO LIST
schtasks /Query /TN "AI Blog - Post Generation" /V /FO LIST
```

After a Windows restart, sign in to the production account and start
`run-ai-blog.bat server` again. The API is not currently installed as a Windows
service. Restrict `API_PORT` with Windows Firewall or place it behind the
production reverse proxy; do not expose the administrative API directly.

### Operations

```bat
run-ai-blog.bat check
run-ai-blog.bat refresh
run-ai-blog.bat generate
run-ai-blog.bat generate-if-due
run-ai-blog.bat server
```

Running `run-ai-blog.bat` without an argument is equivalent to the `server`
mode and never installs scheduled tasks.

To pause production automation without deleting its configuration, run in
PowerShell:

```powershell
Disable-ScheduledTask -TaskName "AI Blog - RSS Refresh"
Disable-ScheduledTask -TaskName "AI Blog - Post Generation"
```

Use `Enable-ScheduledTask` with the same names to resume it. Rerun
`install-schedule` after changing the launcher so Task Scheduler receives the
updated action definitions.

## Development workstation

Create `.env` and `.venv` normally, then use `run-ai-blog.bat` to start only
the API. Do not run `install-schedule`; production automation belongs on the
Windows production machine.

## Optional Linux/systemd deployment

The `systemd/` directory remains available for an optional Linux host. It is
not the primary MAS production configuration. See `systemd/README.md` for its
API service, timers, installation, status, and log commands.

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

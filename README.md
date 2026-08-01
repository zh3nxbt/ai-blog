# AI Blog Backend

Backend service that collects stable manufacturing sources, generates blog posts for MAS Precision Parts, validates them, and stores them in Supabase.

## Runtime

The production workflow has two independent jobs:

1. `python -m blog.refresh_sources` fetches active RSS feeds and stores new, deduplicated source items.
2. `blog/generate.sh` runs the Claude Code CLI with `blog/prompts/generate.md`, validates the result, and saves one post.

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

## Scheduling

Linux deployment units are in `systemd/`:

- `blog-refresh.timer` refreshes RSS sources hourly.
- `blog-generator.timer` starts generation on Monday, Wednesday, and Friday.

Install them with:

```bash
sudo ./systemd/install.sh /opt/blog-backend
sudo systemctl enable --now blog-refresh.timer blog-generator.timer
```

On Windows, use the repository launcher:

```bat
run-ai-blog.bat
```

The launcher validates `.env`, Python, Git Bash, and Claude Code; installs or
updates both Windows scheduled tasks; then runs the FastAPI server in the
foreground. Rerunning it is safe and does not duplicate tasks.

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
is logged on. Authenticate Claude Code under the same account.

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

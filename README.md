# Ralph blog backend

Ralph generates manufacturing blog posts for the MAS Precision Parts website and
stores them in Supabase.

The production workflow has two independent jobs:

- Refresh RSS sources with Python.
- Run Claude Code to select sources, write, validate, and save one idempotent
  blog post.

The old `python -m ralph.ralph_loop` workflow no longer exists. Blog generation
uses `ralph/ralph-generate.sh` and the Claude Code CLI.

## Requirements

- Python 3.12
- Git
- Claude Code CLI
- Access to the existing Supabase project
- A Resend account if email notifications are required

## Native Windows installation

These instructions use Windows 10 or 11, PowerShell, and Git Bash. WSL is not
required. Claude Code uses Git Bash internally on native Windows.

### 1. Install prerequisites

Open PowerShell as your normal Windows user:

```powershell
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3.12 -e --source winget
winget install --id OpenJS.NodeJS.LTS -e --source winget
```

Close and reopen PowerShell, then install Claude Code:

```powershell
npm install -g @anthropic-ai/claude-code
claude doctor
```

If Claude Code cannot locate Git Bash, configure its path and reopen
PowerShell:

```powershell
[Environment]::SetEnvironmentVariable(
    "CLAUDE_CODE_GIT_BASH_PATH",
    "C:\Program Files\Git\bin\bash.exe",
    "User"
)
```

References:

- [Claude Code setup](https://docs.anthropic.com/en/docs/claude-code/getting-started)
- [Git for Windows](https://git-scm.com/install/windows)
- [Python on Windows](https://docs.python.org/3/using/windows.html)

### 2. Clone the repository

Use a short path without spaces. The scheduled-task examples below assume
`C:\ralph\ai-blog`.

```powershell
New-Item -ItemType Directory -Force C:\ralph | Out-Null
Set-Location C:\ralph
git clone https://github.com/zh3nxbt/ai-blog.git
Set-Location .\ai-blog
```

### 3. Create the Python environment

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Never copy a Linux virtual environment. Windows must create its own `.venv`.

### 4. Configure secrets

Copy the existing production `.env` to `C:\ralph\ai-blog\.env` through a secure
channel. Do not commit it.

At minimum, the file needs:

```dotenv
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_KEY=PUBLIC_OR_ANON_KEY
SUPABASE_SECRET=BACKEND_SECRET_OR_SERVICE_ROLE_KEY

EMAIL_PROVIDER=resend
RESEND_API_KEY=...
EMAIL_FROM=...
EMAIL_TO=...
```

`SUPABASE_SECRET` is a backend credential that bypasses Row Level Security.
Never expose it in frontend code or commit it to GitHub. `DATABASE_URL` is only
needed for direct SQL and migration commands.

The database itself does not move to Windows. Ralph continues using the
existing hosted Supabase project and its existing `blog_posts`, source, and
activity tables.

### 5. Authenticate Claude Code

Authenticate as the same Windows user that will own the scheduled task:

```powershell
claude
claude auth status
```

Complete the browser login if prompted. A fresh Windows login is preferred over
copying Linux Claude credential files.

For unattended API-key authentication, configure `ANTHROPIC_API_KEY` in the
scheduled task's environment instead. Do not commit the key.

### 6. Verify the installation

From an activated PowerShell environment:

```powershell
# Verify Python can load configuration.
python -c "from config import settings; print(settings.supabase_url)"

# Read-only database checks.
python -m ralph.generate_helpers check-today
python -m ralph.generate_helpers fetch-sources --rss-limit 2 --topic-limit 1

# Refresh source ingestion. This writes refreshed source items to Supabase.
python -m ralph.refresh_sources
```

Run one manual generation through Git Bash:

```powershell
& "C:\Program Files\Git\bin\bash.exe" `
  -lc 'cd /c/ralph/ai-blog && ./ralph/ralph-generate.sh'
```

Generation is idempotent. If a post already exists for the current UTC date,
Ralph records a skipped result instead of creating a duplicate.

### 7. Configure Windows Task Scheduler

Create both tasks under the Windows user that authenticated Claude Code. Enable
“Run whether user is logged on or not” only after verifying that Claude
authentication is available to that background session.

#### RSS refresh task

- Program: `C:\ralph\ai-blog\.venv\Scripts\python.exe`
- Arguments: `-m ralph.refresh_sources`
- Start in: `C:\ralph\ai-blog`
- Trigger: hourly at minute `05`
- Failure behavior: retry, and retain task history

#### Blog generation task

- Program: `C:\Program Files\Git\bin\bash.exe`
- Arguments: `-lc "cd /c/ralph/ai-blog && ./ralph/ralph-generate.sh"`
- Start in: `C:\ralph\ai-blog`
- Trigger: Monday, Wednesday, and Friday at `14:12 UTC`
- Execution limit: 45 minutes
- Failure behavior: retry, and retain task history

Windows Task Scheduler displays trigger times in local time. Convert
`14:12 UTC` deliberately and account for daylight-saving changes, or select
the synchronization-across-time-zones option.

After creating the tasks, run each one manually and confirm its exit result and
history before retiring the Linux server.

See Microsoft's
[Task Scheduler command documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks)
for automation options.

## Linux installation

Linux remains supported, but it is not required for the Windows deployment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
sudo ./systemd/install.sh
sudo systemctl enable --now ralph-refresh.timer ralph.timer
```

The installer copies `.env` to `/etc/ralph/env`, creates the `ralph` service
user, and generates systemd units with the selected project path.

## Development commands

```powershell
# FastAPI development server
uvicorn api.main:app --reload

# RSS ingestion
python -m ralph.refresh_sources

# Helper command reference
python -m ralph.generate_helpers --help

# Current runtime tests
python -m pytest -q `
  --ignore=tests/test_major_news_screening.py `
  --ignore=tests/test_source_juice.py
```

`tests/test_major_news_screening.py` and `tests/test_source_juice.py` still
target the deleted Python `ralph_content.ralph_loop` implementation. Clean
GitHub `main` already fails those legacy tests; they are not part of the
Claude-CLI runtime and should be removed or rewritten in a separate cleanup.

## Runtime data flow

1. `ralph.refresh_sources` fetches configured RSS feeds and stores new items.
2. `ralph-generate.sh` checks Claude authentication and starts Claude Code.
3. Claude follows `ralph/prompts/generate.md`.
4. Python helper commands read and write Supabase records.
5. Published posts appear on the MAS website through the shared `blog_posts`
   table.
6. Ralph logs the outcome and sends a Resend notification when configured.

## Project structure

```text
ai-blog/
├── api/                       FastAPI application
├── migrations/                Database migrations and verification
├── ralph/
│   ├── generate_helpers.py    JSON CLI used by Claude
│   ├── prompts/generate.md    Generation procedure
│   ├── ralph-generate.sh      Linux and Git-Bash generation entrypoint
│   └── refresh_sources.py     RSS refresh entrypoint
├── ralph_content/             Rendering and remaining content utilities
├── services/                  Supabase, RSS, validation, and email services
├── skills/                    Anti-slop writing instructions
├── systemd/                   Linux service installation
├── tests/
├── config.py
└── requirements.txt
```

## Security and operating rules

- Never commit `.env`, database credentials, Claude credentials, or API keys.
- Backend jobs use `SUPABASE_SECRET`; frontend code must not.
- Use stable RSS, government, standards-body, vendor, and evergreen sources.
- Summarize sources and preserve source links. Do not scrape restricted sites.
- Generation is idempotent and must fail visibly.
- Review logs and database activity after every scheduled-task change.

This project optimizes for boring correctness: explicit behavior, reproducible
inputs, and loud failures.

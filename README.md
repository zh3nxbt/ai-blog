# blog-backend

Backend service that generates one daily blog post for a machine shop website using autonomous AI agents.

## Quick Start

### Setup (DigitalOcean Ubuntu)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual credentials
```

### Development

```bash
# Run API server
uvicorn api.main:app --reload

# Test worker
python worker.py --run-once
```

### Environment Variables

Copy `.env.example` to `.env` and fill in:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon or service key
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude

## Project Structure

```
ai-blog/
├── api/                    # FastAPI application
│   ├── __init__.py
│   └── main.py            # API endpoints
├── services/              # Business logic modules
│   └── __init__.py
├── utils/                 # Helper functions
│   └── __init__.py
├── ralph/                 # Ralph autonomous task execution
│   ├── ralph-once.sh     # Task automation script
│   ├── PRD.md            # Product Requirements Document
│   ├── progress.txt      # Task progress tracking
│   └── README.md         # Ralph documentation
├── docs/                  # Project documentation
│   ├── RALPH_OVERALL_PLAN.md
│   └── RALPH_INTEGRATION_PLAN_REVISED.md
├── worker.py              # Daily generation script
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── claude.md             # Project principles and guidelines
```

## Ralph Autonomous Execution

Ralph is an autonomous task execution system that implements tasks from the PRD one at a time.

### Running Ralph

```bash
./ralph/ralph-once.sh
```

Ralph will:
1. Read project principles from `claude.md`
2. Review the PRD and progress files
3. Pick the next incomplete task (following prioritization order)
4. Create a feature branch for the task
5. Implement the task
6. Commit changes and update progress
7. Create a pull request for review

**Review the PR on GitHub, then merge and run again for the next task.**

See `ralph/README.md` for detailed usage.

## Development Philosophy

This project optimizes for **boring correctness**:
- Stable, legal, reproducible content sources only
- Explicit over clever
- Reliability over elegance
- Fail loudly, never silently

See `claude.md` for full project guidelines and principles.

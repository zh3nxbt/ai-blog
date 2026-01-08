# blog-backend

Backend service that generates one daily blog post for a machine shop website.

## Quick Start

### Setup (WSL2 Ubuntu)

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

# Test worker (won't actually generate until implemented)
python worker.py --run-once
```

### Environment Variables

Copy `.env.example` to `.env` and fill in:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon or service key
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude

## Project Structure

```
blog-backend/
├── api/                    # FastAPI application
│   ├── __init__.py
│   └── main.py            # API endpoints
├── services/              # Business logic modules
│   └── __init__.py
├── utils/                 # Helper functions
│   └── __init__.py
├── tests/                 # Test files
├── worker.py              # Daily generation script
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── claude.md             # Project context for Claude
```

## Next Steps

1. Implement RSS feed fetching in `worker.py`
2. Implement LLM post generation
3. Implement Supabase integration
4. Add tests
5. Set up systemd timer for production

See `claude.md` for full project context and guidelines.

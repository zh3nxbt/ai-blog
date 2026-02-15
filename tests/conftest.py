"""Test bootstrap defaults for required environment variables."""

import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "sb_publishable_test_key")
os.environ.setdefault("SUPABASE_SECRET", "sb_secret_test_key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")

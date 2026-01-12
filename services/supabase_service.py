"""Supabase client service for database operations."""

import os
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.

    Returns:
        Client: Configured Supabase client instance

    Raises:
        ValueError: If required environment variables are missing
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is required")

    if not supabase_key:
        raise ValueError("SUPABASE_KEY environment variable is required")

    return create_client(supabase_url, supabase_key)

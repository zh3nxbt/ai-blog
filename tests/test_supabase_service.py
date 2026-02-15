"""Tests for Supabase service helpers."""

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from services import supabase_service


class _MockInsertQuery:
    def __init__(self, client, payload):
        self._client = client
        self._payload = payload

    def execute(self):
        slug = self._payload["slug"]
        if slug in self._client.existing_slugs:
            raise Exception('duplicate key value violates unique constraint "blog_posts_slug_key"')

        self._client.existing_slugs.add(slug)
        self._client.inserted_slugs.append(slug)
        return SimpleNamespace(data=[{"id": str(uuid4())}])


class _MockTable:
    def __init__(self, client, table_name):
        self._client = client
        self._table_name = table_name

    def insert(self, payload):
        if self._table_name != "blog_posts":
            raise ValueError("Unexpected table in test")
        return _MockInsertQuery(self._client, payload)


class _MockSupabaseClient:
    def __init__(self, existing_slugs):
        self.existing_slugs = set(existing_slugs)
        self.inserted_slugs = []

    def table(self, table_name):
        return _MockTable(self, table_name)


def test_create_blog_post_retries_slug_on_collision(monkeypatch):
    mock_client = _MockSupabaseClient(existing_slugs={"repeated-title"})
    monkeypatch.setattr(supabase_service, "get_supabase_client", lambda: mock_client)

    blog_id = supabase_service.create_blog_post(
        title="Repeated Title",
        content="<p>content</p>",
        status="draft",
    )

    assert isinstance(blog_id, UUID)
    assert mock_client.inserted_slugs == ["repeated-title-2"]


def test_get_supabase_client_requires_service_role_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "anon-only-key")
    monkeypatch.delenv("SUPABASE_SECRET", raising=False)

    with pytest.raises(ValueError) as exc:
        supabase_service.get_supabase_client()

    assert "SUPABASE_SECRET" in str(exc.value)

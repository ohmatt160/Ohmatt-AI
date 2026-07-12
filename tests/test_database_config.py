from app.extensions import normalize_database_url


def test_normalize_legacy_postgres_url_preserves_neon_options():
    url = "postgres://user:pass@host-pooler.neon.tech/app?sslmode=require&channel_binding=require"

    assert normalize_database_url(url) == (
        "postgresql://user:pass@host-pooler.neon.tech/app"
        "?sslmode=require&channel_binding=require"
    )


def test_normalize_database_url_leaves_sqlalchemy_urls_unchanged():
    url = "postgresql://user:pass@host-pooler.neon.tech/app?sslmode=require"

    assert normalize_database_url(url) == url

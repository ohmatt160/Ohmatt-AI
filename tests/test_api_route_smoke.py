import re

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.extensions import Base, get_db
from app.main import create_app


def test_every_documented_api_operation_handles_anonymous_request():
    """Exercise every documented method/path and catch unhandled server errors."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def get_test_db():
        db = test_sessions()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = get_test_db
    paths = app.openapi()["paths"]
    failures = []
    with TestClient(app, raise_server_exceptions=False) as client:
        for path, operations in paths.items():
            request_path = re.sub(r"\{[^}]+}", "1", path)
            for method in operations:
                if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    continue
                response = client.request(method.upper(), request_path)
                if response.status_code >= 500:
                    failures.append(f"{method.upper()} {path} returned {response.status_code}")
    assert not failures, "Unhandled API route errors:\n" + "\n".join(failures)
    engine.dispose()

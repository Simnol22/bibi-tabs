import pytest
from fastapi.testclient import TestClient

from main import BUILD_DIR, app

client = TestClient(app)

needs_build = pytest.mark.skipif(
    not BUILD_DIR.is_dir(), reason="app/ is not built; run `cd app && npm run build`"
)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@needs_build
def test_deep_link_serves_the_spa_shell() -> None:
    """A client-side route has no file on disk and must still return the shell."""
    r = client.get("/song/does-not-exist-on-disk")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


@needs_build
def test_api_routes_win_over_the_static_mount() -> None:
    assert client.get("/health").json() == {"status": "ok"}

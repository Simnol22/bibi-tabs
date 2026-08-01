from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

app = FastAPI(title="BIBI-tabs")

BUILD_DIR = Path(__file__).resolve().parent.parent / "app" / "build"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class SpaFiles(StaticFiles):
    """Static files that fall back to the SPA shell.

    Client-side routes like /song/<id> have no file on disk, so an unmatched
    path must return index.html and let the browser router resolve it.
    """

    async def get_response(self, path: str, scope):  # type: ignore[no-untyped-def]
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


# Mounted last so API routes win. Absent in dev, where vite serves the app
# on :5173 and proxies /api here.
if BUILD_DIR.is_dir():
    app.mount("/", SpaFiles(directory=BUILD_DIR, html=True), name="app")

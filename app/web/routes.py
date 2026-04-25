from pathlib import Path

from fastapi.templating import Jinja2Templates
from starlette.datastructures import Headers

from .._pyc_loader import export_compiled

_WRAPPER_DIR = Path(__file__).resolve().parent
globals().update(export_compiled(__name__, "web/__pycache__/routes.cpython-313.orig.pyc"))


def wants_html(request) -> bool:
    headers = Headers(scope=request.scope)
    accept = headers.get("accept", "")
    lowered = accept.lower()

    if not lowered or lowered == "*/*":
        return True

    if "text/html" in lowered or "application/xhtml+xml" in lowered:
        return True

    return "application/json" not in lowered


templates = Jinja2Templates(directory=str(_WRAPPER_DIR.parent / "templates"))
_compiled_module.templates = templates
_compiled_module.wants_html = wants_html

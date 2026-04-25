from pathlib import Path

from fastapi.templating import Jinja2Templates

from .._pyc_loader import export_compiled

_WRAPPER_DIR = Path(__file__).resolve().parent
globals().update(export_compiled(__name__, "web/__pycache__/routes.cpython-313.orig.pyc"))

templates = Jinja2Templates(directory=str(_WRAPPER_DIR.parent / "templates"))
_compiled_module.templates = templates

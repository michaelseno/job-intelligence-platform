from __future__ import annotations

from importlib.machinery import SourcelessFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import sys
from types import ModuleType


def load_pyc_module(module_name: str, relative_pyc_path: str) -> ModuleType:
    package_root = Path(__file__).resolve().parent
    pyc_path = package_root / relative_pyc_path
    loader = SourcelessFileLoader(module_name, str(pyc_path))
    spec = spec_from_loader(module_name, loader)
    if spec is None:
        raise ImportError(f"Unable to load compiled module spec for {module_name}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


def export_compiled(module_name: str, relative_pyc_path: str) -> dict[str, object]:
    module = load_pyc_module(f"{module_name}.__compiled__", relative_pyc_path)
    exported = {
        key: value
        for key, value in module.__dict__.items()
        if key not in {"__name__", "__loader__", "__package__", "__spec__"}
    }
    exported["_compiled_module"] = module
    return exported

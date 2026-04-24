from __future__ import annotations

from app.adapters.greenhouse.adapter import GreenhouseAdapter
from app.adapters.lever.adapter import LeverAdapter


class UnsupportedAdapterError(ValueError):
    pass


class SourceAdapterRegistry:
    def __init__(self) -> None:
        self._standard = {
            "greenhouse": GreenhouseAdapter(),
            "lever": LeverAdapter(),
        }
        self._common_patterns: dict[str, object] = {}
        self._custom_adapters: dict[str, object] = {}

    def get(self, source_type: str, adapter_key: str | None = None):
        if source_type in self._standard:
            return self._standard[source_type]
        if source_type == "common_pattern":
            if adapter_key and adapter_key in self._common_patterns:
                return self._common_patterns[adapter_key]
            raise UnsupportedAdapterError("Common pattern adapter is not yet approved for this MVP backend pass.")
        if source_type == "custom_adapter":
            if adapter_key and adapter_key in self._custom_adapters:
                return self._custom_adapters[adapter_key]
            raise UnsupportedAdapterError("Custom adapter is not yet approved for this MVP backend pass.")
        raise UnsupportedAdapterError(f"Unsupported source type: {source_type}")

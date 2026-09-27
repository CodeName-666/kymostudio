"""Backward-compatible adapter for the modern CAN receiver."""

from __future__ import annotations

from typing import Any, Dict

from ..can_receiver import CanReceiver


class CanConnection(CanReceiver):
    def __init__(self, channel: Any = "plotter", bustype: str = "virtual") -> None:
        super().__init__({"channel": channel, "interface": bustype, "value_format": "auto"})

    def connect(self) -> bool:
        self.start()
        return self.is_connected()

    def disconnect(self) -> None:
        self.stop()

    def connected(self) -> bool:
        return self.is_connected()

    def config(self, config: Dict[str, Any]) -> None:
        normalized = dict(config or {})
        if "bustype" in normalized and "interface" not in normalized:
            normalized["interface"] = normalized.pop("bustype")
        super().config(normalized)


__all__ = ["CanConnection"]

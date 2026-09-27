"""Backward-compatible adapter for the modern serial receiver."""

from __future__ import annotations

from typing import Any, Dict

from ..serial_receiver import SerialReceiver


class SerialConnection(SerialReceiver):
    def __init__(self, port: str = "", baudrate: int = 115200) -> None:
        super().__init__(
            {
                "port": port,
                "baud": baudrate,
                "size": "8Bit",
                "parity": "None",
                "stop_bits": "1Bit",
            }
        )

    def connect(self) -> bool:
        self.start()
        return self.is_connected()

    def disconnect(self) -> None:
        self.stop()

    def connected(self) -> bool:
        return self.is_connected()

    def config(self, config: Dict[str, Any]) -> None:
        normalized = dict(config or {})
        if "baudrate" in normalized and "baud" not in normalized:
            normalized["baud"] = normalized.pop("baudrate")
        super().config(normalized)


__all__ = ["SerialConnection"]

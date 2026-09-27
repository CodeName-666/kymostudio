"""Backward-compatible adapter for the modern Telnet server receiver."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..telnet_receiver import TelnetServerReceiver


class TelnetServerConnection(TelnetServerReceiver):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config or {"host": "0.0.0.0", "port": 8023})

    def connect(self) -> bool:
        self.start()
        return self.is_connected()

    def disconnect(self) -> None:
        self.stop()

    def connected(self) -> bool:
        return self.is_connected()

    def config(self, config: Dict[str, Any]) -> None:
        super().config(config)


__all__ = ["TelnetServerConnection"]

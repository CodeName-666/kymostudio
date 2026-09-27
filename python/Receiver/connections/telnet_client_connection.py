"""Backward-compatible adapter for the modern Telnet client receiver."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..telnet_receiver import TelnetClientReceiver


class TelnetClientConnection(TelnetClientReceiver):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config or {"host": "localhost", "port": 23})

    def init(self, config: Dict[str, Any]) -> None:
        self.config(config)

    def connect(self) -> bool:
        self.start()
        return self.is_connected()

    def conect(self) -> bool:
        """Compatibility for the misspelled method in the old API."""
        return self.connect()

    def disconnect(self) -> None:
        self.stop()

    def connected(self) -> bool:
        return self.is_connected()


__all__ = ["TelnetClientConnection"]

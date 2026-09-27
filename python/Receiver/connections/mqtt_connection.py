"""Backward-compatible adapter for the modern MQTT receiver."""

from __future__ import annotations

from typing import Any, Dict

from ..mqtt_receiver import MqttReceiver


class MqttConnection(MqttReceiver):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        rx_topic: str = "plotter/rx",
        tx_topic: str = "plotter/tx",
    ) -> None:
        super().__init__(
            {"host": host, "port": port, "rx_topic": rx_topic, "tx_topic": tx_topic}
        )

    def connect(self) -> bool:
        self.start()
        return self.is_connected()

    def disconnect(self) -> None:
        self.stop()

    def connected(self) -> bool:
        return self.is_connected()

    def config(self, config: Dict[str, Any]) -> None:
        super().config(config)


__all__ = ["MqttConnection"]

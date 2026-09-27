"""MQTT receiver implementation built on top of paho-mqtt."""

from __future__ import annotations

import base64
import json
import re
from typing import Any, Callable, Dict, Iterable, Optional

import paho.mqtt.client as mqtt

from Logger import logger

from .receiver import Receiver
from .receiver_thread import ReceiverThread
from .binary_protocol import ProtocolStreamDecoder, is_binary_frame


def normalize_payload(topic: str, payload: bytes) -> bytes:
    """Return a JSON blob containing topic + payload metadata."""

    result: Dict[str, Any] = {"topic": topic or ""}
    payload = payload or b""

    try:
        text = payload.decode("utf-8")
        try:
            result["payload_type"] = "json"
            result["payload"] = json.loads(text)
        except json.JSONDecodeError:
            result["payload_type"] = "text"
            result["payload"] = text
    except UnicodeDecodeError:
        result["payload_type"] = "binary"
        result["payload"] = base64.b64encode(payload).decode("ascii")

    return json.dumps(result).encode("utf-8")


_PLOTTER_FLOAT_RE = re.compile(
    rb"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
)


def _extract_plotter_payload_lines(payload: bytes) -> list[bytes]:
    """Return payload lines that look like PlotterApp datapoints.

    Supports:
    - JSON objects with `id` and (`value` or `y`)
    - Plain numbers (backend treats this as id=0 fallback)
    - Multiple newline-separated datapoints within one MQTT message
    """

    if not payload:
        return []

    if is_binary_frame(payload):
        return ProtocolStreamDecoder(max_buffer_size=max(8192, len(payload))).feed(payload)

    candidates = [line.strip() for line in payload.splitlines() if line.strip()]
    if not candidates:
        return []

    result: list[bytes] = []
    for line in candidates:
        if _PLOTTER_FLOAT_RE.match(line):
            result.append(line)
            continue

        try:
            decoded = json.loads(line.decode("utf-8"))
        except Exception:
            continue

        if not isinstance(decoded, dict):
            continue

        data_id = decoded.get("id")
        value = decoded.get("value")
        if value is None:
            value = decoded.get("y")

        if not isinstance(data_id, int) or not (0 <= data_id <= 255):
            continue
        if not isinstance(value, (int, float)):
            continue

        result.append(line)

    return result


class MqttWorkerThread(ReceiverThread):
    def __init__(
        self,
        host: str,
        port: int,
        rx_topics: Iterable[str],
        qos: int,
        keepalive: int,
        client_id: Optional[str],
        username: Optional[str],
        password: Optional[str],
        tx_topic: Optional[str],
        status_callback: Optional[Callable[[bool], None]] = None,
    ) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._rx_topics = list(rx_topics)
        self._qos = qos
        self._keepalive = keepalive
        self._client_id = client_id
        self._username = username
        self._password = password
        self._tx_topic = tx_topic
        self._status_callback = status_callback
        self._client = mqtt.Client(client_id=self._client_id or None)
        if username:
            self._client.username_pw_set(username, password or None)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._connected = False

    def run(self) -> None:
        logger.log_info("MQTT worker thread started for %s:%s", self._host, self._port)

        while not self.stopped():
            if not self._connected:
                if not self._connect():
                    self.msleep(2000)
                    continue

            rc = self._client.loop(timeout=1.0)
            if rc != mqtt.MQTT_ERR_SUCCESS and not self.stopped():
                logger.log_error("MQTT loop returned error %s", rc)
                self._connected = False
                self._client.disconnect()
                if self._status_callback:
                    self._status_callback(False)

        if self._connected:
            try:
                self._client.disconnect()
            except Exception:
                pass

        if self._status_callback:
            self._status_callback(False)
        logger.log_info("MQTT worker thread stopped")

    def send_response(self, response: bytes) -> None:
        if not self._tx_topic:
            logger.log_warning("MQTT send skipped: tx_topic not configured")
            return
        if not self._connected:
            logger.log_warning("MQTT send skipped: client disconnected")
            return
        result = self._client.publish(self._tx_topic, response, qos=self._qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.log_error("MQTT publish failed with rc=%s", result.rc)

    def stop(self) -> None:
        try:
            self._client.disconnect()
        except Exception:
            pass

    def _connect(self) -> bool:
        try:
            self._client.connect(self._host, self._port, keepalive=self._keepalive)
        except Exception as exc:
            logger.log_warning(f"MQTT connect failed: {exc}")
            return False
        return True

    # MQTT callbacks -------------------------------------------------
    def _on_connect(self, client, userdata, flags, rc):  # pylint: disable=unused-argument
        if rc == 0:
            logger.log_info("MQTT connected to %s:%s", self._host, self._port)
            self._connected = True
            if self._status_callback:
                self._status_callback(True)
            for topic in self._rx_topics:
                if topic:
                    client.subscribe(topic, qos=self._qos)
        else:
            logger.log_error("MQTT connection refused rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc):  # pylint: disable=unused-argument
        if self._status_callback:
            self._status_callback(False)
        if self.stopped():
            logger.log_info("MQTT disconnected")
        else:
            logger.log_warning("MQTT unexpected disconnect rc=%s", rc)
        self._connected = False

    def _on_message(self, client, userdata, message):  # pylint: disable=unused-argument
        plotter_lines = _extract_plotter_payload_lines(message.payload)
        if plotter_lines:
            for line in plotter_lines:
                self.new_data.emit(line)
            return

        normalized = normalize_payload(message.topic, message.payload)
        self.new_data.emit(normalized)


class MqttReceiver(Receiver):
    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(receiver_thread=None)
        self._settings: Dict[str, Any] = defaults.copy() if defaults else {}
        if self._settings:
            super().config(self._settings)

    def config(self, config: Dict[str, Any]) -> None:
        self._settings.update(config or {})
        super().config(self._settings)

    def settings_valid(self) -> bool:
        host = self._settings.get("host")
        port = self._get_port()
        rx_topic = self._settings.get("rx_topic")

        if not host:
            logger.log_warning("MqttReceiver: Missing host")
            return False
        if port is None:
            logger.log_warning("MqttReceiver: Invalid port")
            return False
        if not rx_topic:
            logger.log_warning("MqttReceiver: Missing rx_topic")
            return False

        return True

    def open_connection(self) -> bool:
        if self.receiver_thread is None:
            rx_topics = self._normalize_topics(self._settings.get("rx_topic"))
            worker = MqttWorkerThread(
                host=self._settings.get("host"),
                port=self._get_port() or 1883,
                rx_topics=rx_topics,
                qos=self._get_qos(),
                keepalive=self._get_keepalive(),
                client_id=self._settings.get("client_id"),
                username=self._settings.get("username"),
                password=self._settings.get("password"),
                tx_topic=self._settings.get("tx_topic"),
                status_callback=self._on_worker_status,
            )
            self.attach_thread(worker)

        return True

    def close_connection(self) -> None:
        if self.receiver_thread and self.receiver_thread.isRunning():
            self.receiver_thread.stop_event.emit()
            self.receiver_thread.wait()
        self.detach_thread()
        self._set_connected(False)

    # Helper accessors -----------------------------------------------
    def _get_port(self) -> Optional[int]:
        try:
            port = int(self._settings.get("port", 1883))
        except (TypeError, ValueError):
            return None
        if not (0 < port < 65536):
            return None
        return port

    def _get_qos(self) -> int:
        try:
            qos = int(self._settings.get("qos", 0))
        except (TypeError, ValueError):
            qos = 0
        return min(max(qos, 0), 2)

    def _get_keepalive(self) -> int:
        try:
            keepalive = int(self._settings.get("keepalive", 60))
        except (TypeError, ValueError):
            keepalive = 60
        return max(10, keepalive)

    def _normalize_topics(self, topics: Any) -> Iterable[str]:
        if isinstance(topics, (list, tuple)):
            return [str(topic) for topic in topics if topic]
        return [str(topics)] if topics else []

    def _on_worker_status(self, connected: bool) -> None:
        self._set_connected(connected)


__all__ = ["MqttReceiver", "normalize_payload"]

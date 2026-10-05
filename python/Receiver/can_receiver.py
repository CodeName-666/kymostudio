# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""CAN receiver implementation backed by python-can."""

from __future__ import annotations

import json
import math
import struct
from typing import Any, Dict, Optional

import can

from Logger import logger

from .receiver import Receiver
from .receiver_thread import ReceiverThread
from .binary_protocol import decode_data_frame, is_binary_frame


def decode_can_value(data: bytes, value_format: str = "auto") -> float:
    """Decode CAN payload bytes into the numeric value expected by Kymotrace."""
    payload = bytes(data)
    if not payload:
        raise ValueError("CAN payload is empty")

    normalized_format = (value_format or "auto").lower()
    if normalized_format == "auto":
        normalized_format = {4: "float32_le", 8: "float64_le"}.get(
            len(payload), "uint_le"
        )

    struct_formats = {
        "float32_le": ("<f", 4),
        "float32_be": (">f", 4),
        "float64_le": ("<d", 8),
        "float64_be": (">d", 8),
    }
    if normalized_format in struct_formats:
        format_code, required_length = struct_formats[normalized_format]
        if len(payload) != required_length:
            raise ValueError(
                f"{normalized_format} requires {required_length} bytes, got {len(payload)}"
            )
        value = float(struct.unpack(format_code, payload)[0])
        if not math.isfinite(value):
            raise ValueError("CAN payload decoded to a non-finite value")
        return value

    integer_formats = {
        "uint_le": ("little", False),
        "uint_be": ("big", False),
        "int_le": ("little", True),
        "int_be": ("big", True),
    }
    if normalized_format in integer_formats:
        byte_order, signed = integer_formats[normalized_format]
        return float(int.from_bytes(payload, byteorder=byte_order, signed=signed))

    raise ValueError(f"Unsupported CAN value format: {value_format}")


def can_message_to_kymo_payload(
    message: can.Message, settings: Optional[Dict[str, Any]] = None
) -> bytes:
    """Normalize a python-can message to the backend's JSON wire format."""
    config = settings or {}
    raw_data = bytes(message.data)
    if is_binary_frame(raw_data):
        # CAN-FD can transport the exact v6 frame without an intermediate JSON copy.
        decode_data_frame(raw_data)
        return raw_data
    start_byte = int(config.get("start_byte", 0))
    length = config.get("length")
    selected_data = raw_data[start_byte:]
    if length not in (None, ""):
        selected_data = selected_data[: int(length)]

    value = decode_can_value(selected_data, str(config.get("value_format", "auto")))
    value = value * float(config.get("scale", 1.0)) + float(config.get("offset", 0.0))

    configured_id = config.get("data_id")
    data_id = int(configured_id) if configured_id not in (None, "") else int(message.arbitration_id) & 0xFF
    if not 0 <= data_id <= 255:
        raise ValueError(f"CAN data_id must be between 0 and 255, got {data_id}")

    payload: Dict[str, Any] = {
        "id": data_id,
        "value": value,
        "can_id": int(message.arbitration_id),
    }
    if message.timestamp and math.isfinite(float(message.timestamp)):
        payload["timestamp"] = float(message.timestamp)
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


class CanWorkerThread(ReceiverThread):
    """Receive CAN frames without blocking the Qt GUI thread."""

    def __init__(self, bus: can.BusABC, settings: Dict[str, Any]) -> None:
        super().__init__()
        self._bus = bus
        self._settings = settings.copy()
        self._receive_timeout = max(0.01, float(settings.get("receive_timeout", 0.2)))

    def run(self) -> None:
        logger.log_info("CAN worker thread started")
        while not self.stopped():
            try:
                message = self._bus.recv(timeout=self._receive_timeout)
            except (can.CanError, OSError) as exc:
                if not self.stopped():
                    logger.log_error(f"CAN receive failed: {exc}")
                break

            if message is None:
                continue

            try:
                payload = can_message_to_kymo_payload(message, self._settings)
            except (TypeError, ValueError, struct.error) as exc:
                logger.log_warning(f"Ignoring invalid CAN frame {message.arbitration_id:#x}: {exc}")
                continue
            self.publish([payload])
        logger.log_info("CAN worker thread stopped")

    def send_response(self, response: bytes) -> None:
        tx_id = self._settings.get("tx_id")
        if tx_id in (None, ""):
            raise ValueError("CAN tx_id is required before sending a response")

        arbitration_id = int(str(tx_id), 0) if isinstance(tx_id, str) else int(tx_id)
        message = can.Message(
            arbitration_id=arbitration_id,
            data=bytes(response),
            is_extended_id=bool(
                self._settings.get("is_extended_id", arbitration_id > 0x7FF)
            ),
            is_fd=bool(self._settings.get("fd", False)),
        )
        self._bus.send(message, timeout=float(self._settings.get("send_timeout", 1.0)))

    def stop(self) -> None:
        super().stop()
        try:
            self._bus.shutdown()
        except (can.CanError, OSError):
            pass


class CanReceiver(Receiver):
    """Concrete receiver for SocketCAN, PCAN, virtual buses, and other backends."""

    VALUE_FORMATS = {
        "auto",
        "float32_le",
        "float32_be",
        "float64_le",
        "float64_be",
        "uint_le",
        "uint_be",
        "int_le",
        "int_be",
    }

    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(receiver_thread=None)
        self._settings: Dict[str, Any] = defaults.copy() if defaults else {}
        self._bus: Optional[can.BusABC] = None
        self._worker: Optional[CanWorkerThread] = None
        if self._settings:
            super().config(self._settings)

    def config(self, config: Dict[str, Any]) -> None:
        self._settings.update(config or {})
        super().config(self._settings)

    def settings_valid(self) -> bool:
        interface = self._settings.get("interface") or self._settings.get("bustype")
        channel = self._settings.get("channel")
        if not interface or channel in (None, ""):
            logger.log_warning("CanReceiver: interface and channel are required")
            return False

        try:
            if self._settings.get("bitrate") not in (None, ""):
                if int(self._settings["bitrate"]) <= 0:
                    return False
            if float(self._settings.get("scale", 1.0)) == 0:
                logger.log_warning("CanReceiver: scale must not be zero")
                return False
            if int(self._settings.get("start_byte", 0)) < 0:
                return False
            if self._settings.get("length") not in (None, "") and int(self._settings["length"]) <= 0:
                return False
            if str(self._settings.get("value_format", "auto")).lower() not in self.VALUE_FORMATS:
                return False
        except (TypeError, ValueError):
            return False
        return True

    def open_connection(self) -> bool:
        if self.is_connected():
            return True
        if not self.settings_valid():
            return False

        interface = str(self._settings.get("interface") or self._settings.get("bustype"))
        kwargs: Dict[str, Any] = {
            "interface": interface,
            "channel": self._settings.get("channel"),
        }
        if self._settings.get("bitrate") not in (None, ""):
            kwargs["bitrate"] = int(self._settings["bitrate"])
        if "fd" in self._settings:
            kwargs["fd"] = bool(self._settings["fd"])
        if "receive_own_messages" in self._settings:
            kwargs["receive_own_messages"] = bool(self._settings["receive_own_messages"])

        try:
            bus = can.Bus(**kwargs)
        except (can.CanError, OSError, TypeError, ValueError) as exc:
            logger.log_error(f"CanReceiver: Cannot open {interface} bus: {exc}")
            return False

        self._bus = bus
        self._worker = CanWorkerThread(bus, self._settings)
        self.attach_thread(self._worker)
        self._set_connected(True)
        logger.log_info("CanReceiver connected via %s on %s", interface, kwargs["channel"])
        return True

    def close_connection(self) -> None:
        self._worker = None
        self.detach_thread()
        if self._bus is not None:
            try:
                self._bus.shutdown()
            except (can.CanError, OSError):
                pass
            self._bus = None
        self._set_connected(False)
        logger.log_info("CanReceiver disconnected")


__all__ = [
    "CanReceiver",
    "CanWorkerThread",
    "can_message_to_kymo_payload",
    "decode_can_value",
]

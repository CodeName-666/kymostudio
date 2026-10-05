"""Strict, bounded parsing of the existing JSON, numeric and binary formats.

No Qt, logging or UI callbacks live here. Callers decide how to report a
ProtocolError; comment and blank lines intentionally return None.
"""
from __future__ import annotations

import json
from typing import Any

from Receiver.binary_protocol import ProtocolError, decode_data_frame, is_binary_frame
from Receiver.message import PlotDataPoint

MAX_PAYLOAD_BYTES = 65536


def _record(decoded: Any) -> PlotDataPoint:
    if type(decoded) in (float, int):
        return PlotDataPoint(id=0, value=decoded)
    if not isinstance(decoded, dict):
        raise ValueError("Expected a numeric value or a measurement object")
    value = decoded.get("value")
    if value is None:
        value = decoded.get("y")
    return PlotDataPoint(
        id=decoded.get("id"), value=value, x=decoded.get("x"),
        timestamp=decoded.get("timestamp"), z_value=decoded.get("z"),
    )


def _decode_text(text: str, depth: int = 0) -> PlotDataPoint | None:
    text = text.strip()
    if not text or text.startswith("#"):
        return None
    if depth > 2:
        raise ValueError("Nested payload wrappers exceed the limit")
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        decoded = float(text)  # Preserve the existing '+1.0' numeric fallback.
    if isinstance(decoded, dict) and {"topic", "payload_type", "payload"} <= decoded.keys():
        kind, payload = decoded["payload_type"], decoded["payload"]
        if kind == "json" and isinstance(payload, dict):
            return _record(payload)
        if kind == "text" and isinstance(payload, str):
            return _decode_text(payload, depth + 1)
        raise ValueError("Invalid MQTT measurement wrapper")
    return _record(decoded)


def parse_payload(payload: bytes) -> PlotDataPoint | None:
    """Parse one complete wire message or raise :class:`ProtocolError`.

    Binary stream framing belongs to ProtocolStreamDecoder; this function does
    not concatenate fragments. Its input bound also prevents accidental UI
    stalls from oversized MQTT/TCP/serial messages.
    """
    if not isinstance(payload, (bytes, bytearray)):
        raise ProtocolError("Payload must be bytes")
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ProtocolError(f"Payload exceeds {MAX_PAYLOAD_BYTES} bytes")
    if not payload:
        return None
    if is_binary_frame(payload):
        return decode_data_frame(payload)
    try:
        return _decode_text(payload.decode("utf-8-sig"))
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError) as exc:
        raise ProtocolError(f"Invalid measurement: {exc}") from exc

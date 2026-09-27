"""Compact Plotter Binary Protocol v6 codec and stream framing.

The module is the protocol seam shared by transport adapters and the backend.
It deliberately exposes only point encoding/decoding and incremental framing;
wire-layout details remain local to this implementation.
"""

from __future__ import annotations

import math
import struct
from typing import Final

from .message import PlotDataPoint


SYNC: Final = b"\xA5\x5A"
WIRE_VERSION: Final = 1
PROTOCOL_VERSION: Final = "6.0"

_VERSION_SHIFT: Final = 6
_VERSION_MASK: Final = 0xC0
_TYPE_MASK: Final = 0x30
_TYPE_DATA: Final = 0x00
_FLAG_X: Final = 0x08
_FLAG_Z: Final = 0x04
_FLAG_TIMESTAMP: Final = 0x02
_RESERVED_MASK: Final = 0x01
_BASE_DESCRIPTOR: Final = WIRE_VERSION << _VERSION_SHIFT
_MIN_FRAME_SIZE: Final = 9
_MAX_FRAME_SIZE: Final = 21


class ProtocolError(ValueError):
    """Raised when a complete wire frame violates the protocol contract."""


def crc8(data: bytes) -> int:
    """Return CRC-8/ATM (poly 0x07, init 0x00) without a lookup table."""
    checksum = 0
    for byte in data:
        checksum ^= byte
        for _ in range(8):
            checksum = (
                ((checksum << 1) ^ 0x07) & 0xFF
                if checksum & 0x80
                else (checksum << 1) & 0xFF
            )
    return checksum


def encode_data_point(point: PlotDataPoint) -> bytes:
    """Encode one point into a 9–21 byte little-endian binary frame."""
    descriptor = _BASE_DESCRIPTOR | _TYPE_DATA
    fields: list[bytes] = []

    if point.x is not None:
        descriptor |= _FLAG_X
        fields.append(_pack_finite_float(point.x, "x"))

    fields.append(_pack_finite_float(point.value, "value"))

    if point.z_value is not None:
        descriptor |= _FLAG_Z
        fields.append(_pack_finite_float(point.z_value, "z"))

    if point.timestamp is not None:
        descriptor |= _FLAG_TIMESTAMP
        timestamp = float(point.timestamp)
        if not math.isfinite(timestamp) or timestamp < 0:
            raise ValueError("timestamp must be a finite, non-negative number")
        timestamp_ms = round(timestamp * 1000.0)
        if timestamp_ms > 0xFFFFFFFF:
            raise ValueError("timestamp exceeds the uint32 millisecond range")
        fields.append(struct.pack("<I", timestamp_ms))

    body = bytes((descriptor, point.id)) + b"".join(fields)
    return SYNC + body + bytes((crc8(body),))


def decode_data_frame(frame: bytes) -> PlotDataPoint:
    """Decode and validate one complete binary data frame."""
    raw = bytes(frame)
    if len(raw) < _MIN_FRAME_SIZE:
        raise ProtocolError("binary frame is incomplete")
    if not raw.startswith(SYNC):
        raise ProtocolError("binary frame has an invalid sync marker")

    descriptor = raw[2]
    expected_length = frame_length_from_descriptor(descriptor)
    if len(raw) != expected_length:
        raise ProtocolError(
            f"binary frame length mismatch: expected {expected_length}, got {len(raw)}"
        )
    if crc8(raw[2:-1]) != raw[-1]:
        raise ProtocolError("binary frame CRC mismatch")

    offset = 4
    x_value = None
    if descriptor & _FLAG_X:
        x_value = _unpack_float(raw, offset, "x")
        offset += 4

    value = _unpack_float(raw, offset, "value")
    offset += 4

    z_value = None
    if descriptor & _FLAG_Z:
        z_value = _unpack_float(raw, offset, "z")
        offset += 4

    timestamp = None
    if descriptor & _FLAG_TIMESTAMP:
        timestamp = struct.unpack_from("<I", raw, offset)[0] / 1000.0

    return PlotDataPoint(
        id=raw[3],
        value=value,
        x=x_value,
        timestamp=timestamp,
        z_value=z_value,
    )


def frame_length_from_descriptor(descriptor: int) -> int:
    """Return the deterministic frame size encoded by a data descriptor."""
    version = (descriptor & _VERSION_MASK) >> _VERSION_SHIFT
    if version != WIRE_VERSION:
        raise ProtocolError(f"unsupported binary wire version: {version}")
    if descriptor & _TYPE_MASK != _TYPE_DATA:
        raise ProtocolError("unsupported binary message type")
    if descriptor & _RESERVED_MASK:
        raise ProtocolError("reserved descriptor bit must be zero")

    optional_fields = int(bool(descriptor & _FLAG_X))
    optional_fields += int(bool(descriptor & _FLAG_Z))
    optional_fields += int(bool(descriptor & _FLAG_TIMESTAMP))
    return _MIN_FRAME_SIZE + optional_fields * 4


def is_binary_frame(payload: bytes) -> bool:
    return len(payload) >= len(SYNC) and payload.startswith(SYNC)


class ProtocolStreamDecoder:
    """Incrementally split a byte stream into binary frames or JSON lines."""

    def __init__(self, max_buffer_size: int = 8192) -> None:
        if max_buffer_size < _MAX_FRAME_SIZE:
            raise ValueError("max_buffer_size is too small for a protocol frame")
        self._buffer = bytearray()
        self._max_buffer_size = max_buffer_size

    def reset(self) -> None:
        self._buffer.clear()

    def feed(self, chunk: bytes) -> list[bytes]:
        if chunk:
            self._buffer.extend(chunk)

        messages: list[bytes] = []
        while self._buffer:
            if self._buffer.startswith(SYNC):
                if len(self._buffer) < 4:
                    break
                try:
                    frame_length = frame_length_from_descriptor(self._buffer[2])
                except ProtocolError:
                    del self._buffer[0]
                    continue
                if len(self._buffer) < frame_length:
                    break

                candidate = bytes(self._buffer[:frame_length])
                try:
                    decode_data_frame(candidate)
                except ProtocolError:
                    del self._buffer[0]
                    continue
                messages.append(candidate)
                del self._buffer[:frame_length]
                continue

            newline_index = self._buffer.find(b"\n")
            sync_index = self._buffer.find(SYNC)

            if newline_index >= 0 and (sync_index < 0 or newline_index < sync_index):
                line = bytes(self._buffer[:newline_index]).rstrip(b"\r")
                del self._buffer[: newline_index + 1]
                if line:
                    messages.append(line)
                continue

            if sync_index > 0:
                del self._buffer[:sync_index]
                continue

            if len(self._buffer) > self._max_buffer_size:
                # Retain a possible partial sync marker at the end.
                keep = 1 if self._buffer[-1] == SYNC[0] else 0
                if keep:
                    self._buffer[:] = self._buffer[-1:]
                else:
                    self._buffer.clear()
            break

        return messages


def _pack_finite_float(value: float, field: str) -> bytes:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{field} must be finite")
    try:
        return struct.pack("<f", numeric)
    except OverflowError as exc:
        raise ValueError(f"{field} exceeds the float32 range") from exc


def _unpack_float(frame: bytes, offset: int, field: str) -> float:
    value = float(struct.unpack_from("<f", frame, offset)[0])
    if not math.isfinite(value):
        raise ProtocolError(f"binary {field} is not finite")
    return value


__all__ = [
    "PROTOCOL_VERSION",
    "ProtocolError",
    "ProtocolStreamDecoder",
    "SYNC",
    "crc8",
    "decode_data_frame",
    "encode_data_point",
    "frame_length_from_descriptor",
    "is_binary_frame",
]

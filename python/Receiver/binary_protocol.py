"""Compact Kymotrace Binary Protocol v6 codec and stream framing.

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
PROTOCOL_VERSION: Final = "6.1"

_VERSION_SHIFT: Final = 6
_VERSION_MASK: Final = 0xC0
_TYPE_MASK: Final = 0x30
_TYPE_DATA: Final = 0x00
_FLAG_X: Final = 0x08
_FLAG_Z: Final = 0x04
_FLAG_TIMESTAMP: Final = 0x02
_FLAG_NO_CRC: Final = 0x01
_BASE_DESCRIPTOR: Final = WIRE_VERSION << _VERSION_SHIFT
_MIN_FRAME_SIZE: Final = 9
_MAX_FRAME_SIZE: Final = 21


class ProtocolError(ValueError):
    """Raised when a complete wire frame violates the protocol contract."""


def _crc8_bitwise(byte: int) -> int:
    checksum = byte
    for _ in range(8):
        checksum = ((checksum << 1) ^ 0x07) & 0xFF if checksum & 0x80 else (checksum << 1) & 0xFF
    return checksum


# Per-byte lookup: one index per input byte instead of eight shift/xor steps.
_CRC8_TABLE: Final = tuple(_crc8_bitwise(value) for value in range(256))


def crc8(data: bytes) -> int:
    """Return CRC-8/ATM (poly 0x07, init 0x00)."""
    checksum = 0
    table = _CRC8_TABLE
    for byte in data:
        checksum = table[checksum ^ byte]
    return checksum


def encode_data_point(point: PlotDataPoint, *, crc_enabled: bool = False) -> bytes:
    """Encode 9–21 bytes; CRC is opt-in, otherwise emit NO_CRC and a zero trailer."""
    descriptor = _BASE_DESCRIPTOR | _TYPE_DATA
    if not crc_enabled:
        descriptor |= _FLAG_NO_CRC
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
    return SYNC + body + bytes((crc8(body) if crc_enabled else 0,))


def decode_data_frame(frame: bytes) -> PlotDataPoint:
    """Decode and validate one complete binary data frame."""
    raw = frame if type(frame) is bytes else bytes(frame)
    if len(raw) < _MIN_FRAME_SIZE:
        raise ProtocolError("binary frame is incomplete")
    if not raw.startswith(SYNC):
        raise ProtocolError("binary frame has an invalid sync marker")

    layout = _LAYOUTS.get(raw[2])
    if layout is None:
        frame_length_from_descriptor(raw[2])  # raises the specific descriptor error
    expected_length, unpacker, has_x, has_z, has_timestamp = layout
    if len(raw) != expected_length:
        raise ProtocolError(
            f"binary frame length mismatch: expected {expected_length}, got {len(raw)}"
        )
    if not raw[2] & _FLAG_NO_CRC and crc8(raw[2:-1]) != raw[-1]:
        raise ProtocolError("binary frame CRC mismatch")

    fields = unpacker.unpack_from(raw, 4)
    if not (has_x or has_z or has_timestamp):
        # Most common frame (ID + value): skip the generic field walk.
        if not math.isfinite(fields[0]):
            raise ProtocolError("binary value is not finite")
        return PlotDataPoint(id=raw[3], value=fields[0])

    fields = iter(fields)
    x_value = next(fields) if has_x else None
    value = next(fields)
    z_value = next(fields) if has_z else None
    timestamp = next(fields) / 1000.0 if has_timestamp else None
    for name, number in (("x", x_value), ("value", value), ("z", z_value)):
        if number is not None and not math.isfinite(number):
            raise ProtocolError(f"binary {name} is not finite")

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

    optional_fields = int(bool(descriptor & _FLAG_X))
    optional_fields += int(bool(descriptor & _FLAG_Z))
    optional_fields += int(bool(descriptor & _FLAG_TIMESTAMP))
    return _MIN_FRAME_SIZE + optional_fields * 4


def _layout(descriptor: int) -> tuple[int, struct.Struct, bool, bool, bool]:
    has_x, has_z, has_timestamp = (bool(descriptor & flag) for flag in (_FLAG_X, _FLAG_Z, _FLAG_TIMESTAMP))
    fmt = "<" + "f" * has_x + "f" + "f" * has_z + "I" * has_timestamp
    return frame_length_from_descriptor(descriptor), struct.Struct(fmt), has_x, has_z, has_timestamp


# Every valid data descriptor, precomputed: one dict lookup and one unpack per frame.
_LAYOUTS: Final = {}
for _descriptor in range(256):
    try:
        _LAYOUTS[_descriptor] = _layout(_descriptor)
    except ProtocolError:
        pass
_FRAME_LENGTHS: Final = {descriptor: layout[0] for descriptor, layout in _LAYOUTS.items()}


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
        buffer = self._buffer
        if chunk:
            buffer.extend(chunk)

        # Scan with a read position and trim once: deleting after every frame
        # would move the remaining buffer for each message.
        messages: list[bytes] = []
        frame_lengths = _FRAME_LENGTHS
        table = _CRC8_TABLE
        pos, size = 0, len(buffer)
        while pos < size:
            if buffer.startswith(SYNC, pos):
                if size - pos < 4:
                    break
                frame_length = frame_lengths.get(buffer[pos + 2])
                if frame_length is None:
                    pos += 1
                    continue
                if size - pos < frame_length:
                    break
                if not buffer[pos + 2] & _FLAG_NO_CRC:
                    checksum = 0
                    for byte in buffer[pos + 2:pos + frame_length - 1]:
                        checksum = table[checksum ^ byte]
                    if checksum != buffer[pos + frame_length - 1]:
                        pos += 1
                        continue
                # Field validation (finite values) happens in decode_data_frame.
                messages.append(bytes(buffer[pos:pos + frame_length]))
                pos += frame_length
                continue

            newline_index = buffer.find(b"\n", pos)
            sync_index = buffer.find(SYNC, pos)

            if newline_index >= 0 and (sync_index < 0 or newline_index < sync_index):
                line = bytes(buffer[pos:newline_index]).rstrip(b"\r")
                pos = newline_index + 1
                if line:
                    messages.append(line)
                continue

            if sync_index > pos:
                pos = sync_index
                continue

            if size - pos > self._max_buffer_size:
                # Retain a possible partial sync marker at the end.
                pos = size - 1 if buffer[-1] == SYNC[0] else size
            break

        del buffer[:pos]
        return messages


def _pack_finite_float(value: float, field: str) -> bytes:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{field} must be finite")
    try:
        return struct.pack("<f", numeric)
    except OverflowError as exc:
        raise ValueError(f"{field} exceeds the float32 range") from exc


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

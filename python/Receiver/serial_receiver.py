# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Serial receiver implementation backed by PySerial."""

from __future__ import annotations

from typing import Any, Dict, Optional

import serial
from serial import SerialException
from serial.tools import list_ports

from Logger import logger

from .receiver import Receiver
from .receiver_thread import ReceiverThread
from .binary_protocol import ProtocolStreamDecoder


def available_serial_ports() -> Dict[str, str]:
    """Return a mapping of discovered COM port names to their descriptions."""

    ports = {}
    for port in list_ports.comports():
        if port.name:
            ports[port.name] = port.description or port.name
    return ports


class SerialWorkerThread(ReceiverThread):
    """Background thread that continuously reads from the serial port."""

    def __init__(self, serial_port: serial.Serial) -> None:
        super().__init__()
        self._serial = serial_port
        self._protocol_decoder = ProtocolStreamDecoder()

    def run(self) -> None:
        logger.log_info("Serial worker thread started")
        while not self.stopped():
            try:
                waiting = self._serial.in_waiting
                payload = self._serial.read(min(max(waiting, 1), 4096))
            except SerialException as exc:
                logger.log_error(f"Serial worker read failed: {exc}")
                break
            except OSError as exc:
                logger.log_error(f"Serial worker OS error: {exc}")
                break

            if not payload:
                continue

            self.publish(self._protocol_decoder.feed(payload))

        logger.log_info("Serial worker thread stopped")

    def send_response(self, response: bytes) -> None:
        try:
            self._serial.write(response)
        except SerialException as exc:
            logger.log_error(f"Serial send failed: {exc}")

    def stop(self) -> None:
        super().stop()
        try:
            if self._serial.is_open:
                self._serial.close()
        except SerialException:
            pass


class SerialReceiver(Receiver):
    """Serial implementation of the generic :class:`Receiver` contract."""

    BYTE_SIZES = {
        "5Bit": serial.FIVEBITS,
        "6Bit": serial.SIXBITS,
        "7Bit": serial.SEVENBITS,
        "8Bit": serial.EIGHTBITS,
    }
    PARITY = {
        "None": serial.PARITY_NONE,
        "Even": serial.PARITY_EVEN,
        "Odd": serial.PARITY_ODD,
        "Mark": serial.PARITY_MARK,
        "Space": serial.PARITY_SPACE,
    }
    STOP_BITS = {
        "1Bit": serial.STOPBITS_ONE,
        "1.5Bit": serial.STOPBITS_ONE_POINT_FIVE,
        "2Bit": serial.STOPBITS_TWO,
        "1": serial.STOPBITS_ONE,
        "2": serial.STOPBITS_TWO,
    }

    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(receiver_thread=None)
        self._settings: Dict[str, Any] = defaults.copy() if defaults else {}
        self._serial: Optional[serial.Serial] = None
        self._worker: Optional[SerialWorkerThread] = None
        if self._settings:
            super().config(self._settings)

    def config(self, config: Dict[str, Any]) -> None:
        self._settings.update(config or {})
        super().config(self._settings)

    def settings_valid(self) -> bool:
        if not self._settings:
            logger.log_warning("SerialReceiver: No settings supplied")
            return False

        port = self._settings.get("port")
        baud = self._settings.get("baud")
        size = self._settings.get("size")
        parity = self._settings.get("parity")
        stop_bits = self._settings.get("stop_bits") or self._settings.get("stop")

        if not port:
            logger.log_warning("SerialReceiver: Missing COM port")
            return False

        if baud in (None, ""):
            logger.log_warning("SerialReceiver: Missing baud rate")
            return False

        try:
            baud_value = int(baud)
            if baud_value <= 0:
                raise ValueError
        except (ValueError, TypeError):
            logger.log_warning("SerialReceiver: Invalid baud value %s", baud)
            return False

        if size not in self.BYTE_SIZES:
            logger.log_warning("SerialReceiver: Unsupported byte size %s", size)
            return False

        if parity not in self.PARITY:
            logger.log_warning("SerialReceiver: Unsupported parity %s", parity)
            return False

        if stop_bits not in self.STOP_BITS:
            logger.log_warning("SerialReceiver: Unsupported stop bits %s", stop_bits)
            return False

        available = available_serial_ports().keys()
        if available and port not in available:
            logger.log_warning("SerialReceiver: Port %s not found", port)
            return False

        return True

    def open_connection(self) -> bool:
        if self.is_connected():
            return True

        try:
            serial_port = serial.Serial(
                port=self._settings.get("port"),
                baudrate=int(self._settings.get("baud", 0)),
                bytesize=self.BYTE_SIZES.get(self._settings.get("size"), serial.EIGHTBITS),
                parity=self.PARITY.get(self._settings.get("parity"), serial.PARITY_NONE),
                stopbits=self.STOP_BITS.get(
                    self._settings.get("stop_bits") or self._settings.get("stop"),
                    serial.STOPBITS_ONE,
                ),
                timeout=1,
            )
        except (SerialException, ValueError) as exc:
            logger.log_error(f"SerialReceiver: Cannot open port: {exc}")
            return False

        serial_port.reset_input_buffer()
        serial_port.reset_output_buffer()

        self._serial = serial_port
        self._worker = SerialWorkerThread(serial_port)
        self.attach_thread(self._worker)
        self._set_connected(True)
        logger.log_info("SerialReceiver connected to %s", serial_port.portstr)
        return True

    def close_connection(self) -> None:
        # Receiver.stop() handles thread termination. Ensure instance references are released.
        self._worker = None
        self.detach_thread()

        if self._serial:
            try:
                if self._serial.is_open:
                    self._serial.close()
            except SerialException as exc:
                logger.log_warning(f"SerialReceiver close error: {exc}")
            finally:
                self._serial = None

        self._set_connected(False)
        logger.log_info("SerialReceiver disconnected")


__all__ = ["SerialReceiver", "available_serial_ports"]

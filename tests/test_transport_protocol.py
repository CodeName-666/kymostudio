"""Wire transport integration: requires the real Qt and transport libraries."""
from __future__ import annotations
import pytest
pytest.importorskip("PySide6", reason="Install requirements-dev.txt to run Qt integration tests")
pytest.importorskip("can", reason="python-can transport dependency missing")
pytest.importorskip("serial", reason="pyserial transport dependency missing")
pytest.importorskip("paho.mqtt.client", reason="paho-mqtt transport dependency missing")

import unittest
from Receiver.binary_protocol import encode_data_point
from Receiver.message import PlotDataPoint
from Backend.backend import Backend  # noqa: E402
from Receiver.mqtt_receiver import _extract_plotter_payload_lines  # noqa: E402
from Receiver.serial_receiver import SerialReceiver  # noqa: E402
from Receiver.can_receiver import can_message_to_plotter_payload  # noqa: E402
import can  # noqa: E402


class TransportIntegrationTests(unittest.TestCase):
    def test_backend_parser_accepts_binary_without_json_conversion(self) -> None:
        point = PlotDataPoint(id=12, x=2.0, value=3.0, timestamp=4.0)
        parsed = Backend._parse_data_point(object(), "Serial", encode_data_point(point))
        self.assertEqual(parsed, point)

    def test_mqtt_message_can_contain_concatenated_binary_frames(self) -> None:
        first = encode_data_point(PlotDataPoint(id=1, value=1.0))
        second = encode_data_point(PlotDataPoint(id=2, value=2.0))
        self.assertEqual(_extract_plotter_payload_lines(first + second), [first, second])

    def test_serial_receiver_never_strips_binary_crc_bytes(self) -> None:
        frame = encode_data_point(PlotDataPoint(id=10, value=-8.0))
        self.assertEqual(SerialReceiver._parse_payload(object(), frame), frame)

    def test_can_fd_forwards_the_same_binary_frame(self) -> None:
        frame = encode_data_point(PlotDataPoint(id=9, x=1.0, value=2.0))
        message = can.Message(arbitration_id=0x123, data=frame, is_fd=True)
        self.assertEqual(can_message_to_plotter_payload(message), frame)

    def test_legacy_json_rejects_non_finite_values_like_binary(self) -> None:
        class ParserContext:
            _invalid_total = 0
            _parse_warning_times = {}
            def _notify_status(self, *_args) -> None:
                pass

        self.assertIsNone(
            Backend._parse_data_point(
                ParserContext(), "Serial", b'{"id":1,"value":NaN}'
            )
        )



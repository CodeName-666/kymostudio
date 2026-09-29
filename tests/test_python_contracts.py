"""Regression tests for Python interfaces consumed by the QML application."""

from __future__ import annotations

import pytest
pytest.importorskip("PySide6", reason="Install requirements-dev.txt to run Qt integration tests")
pytest.importorskip("can", reason="python-can transport dependency missing")
pytest.importorskip("serial", reason="pyserial transport dependency missing")
pytest.importorskip("paho.mqtt.client", reason="paho-mqtt transport dependency missing")

import inspect
import io
import json
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
from contextlib import redirect_stdout

import can
from PySide6.QtCore import QCoreApplication


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from Backend.Charts import (  # noqa: E402
    ChartFactory,
    ChartType,
    TimeSeriesChart,
    XYLineChart,
    XYScatterChart,
    XYZScatterChart,
)
from Backend.backend import Backend, ConnectionInfo  # noqa: E402
from Receiver.can_receiver import (  # noqa: E402
    CanReceiver,
    can_message_to_plotter_payload,
    decode_can_value,
)
from Receiver.connections.can_connection import CanConnection  # noqa: E402
from Receiver.connections.mqtt_connection import MqttConnection  # noqa: E402
from Receiver.connections.serial_connection import SerialConnection  # noqa: E402
from Receiver.connections.telnet_client_connection import TelnetClientConnection  # noqa: E402
from Receiver.connections.telnet_server_connection import TelnetServerConnection  # noqa: E402
from Receiver.registry import ReceiverRegistry  # noqa: E402
from Receiver.test_receiver import TestReceiver as SyntheticReceiver  # noqa: E402
from Core.paths import user_config_path
from Logger.logger import Logger, log_info  # noqa: E402


class BackendCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self) -> None:
        Backend._Backend__backend_instance = None
        self.backend = Backend()
        self.backend._load_connections_from_config = Mock()
        self.backend.config(
            {
                "interfaces": [
                    {
                        "type": "Test",
                        "default": {"type": "Sinus", "sample_ms": 50},
                    }
                ],
                "qml": {"interfaces": ["Test"]},
            }
        )

    def tearDown(self) -> None:
        for connection in self.backend._Backend__connections.values():
            if connection.receiver and connection.receiver.is_connected():
                connection.receiver.stop()
        self.backend._batch_timer.stop()
        self.backend._Backend__com_updater_timer.stop()
        self.backend._Backend__scroll_timer.stop()
        Backend._Backend__backend_instance = None

    def test_legacy_provider_methods_use_the_current_interface(self) -> None:
        settings = self.backend.get_settings("Test")
        settings["sample_ms"] = 999
        self.assertEqual(self.backend.get_settings("Test")["sample_ms"], 50)

        self.backend.interface = "Test"
        self.assertTrue(self.backend.settings_valid())
        self.assertTrue(self.backend.settings_valid("Test"))
        self.assertFalse(self.backend.settings_valid("Unknown"))

        receiver = SyntheticReceiver({"type": "Sinus", "sample_ms": 50})
        self.backend._Backend__connections["test-1"] = ConnectionInfo(
            connection_id="test-1",
            interface_type="Test",
            display_name="Compatibility Test",
            status="disconnected",
            receiver=receiver,
        )

        self.assertTrue(self.backend.connect_selected())
        self.assertTrue(self.backend.is_connect())
        self.assertTrue(self.backend.connected())
        self.assertTrue(self.backend.disconnectFrom("Test"))
        self.assertFalse(self.backend.connected())

    def test_persistent_config_path_is_independent_of_working_directory(self) -> None:
        config_path = Path(self.backend._Backend__config_path)
        self.assertTrue(config_path.is_absolute())
        self.assertEqual(config_path, user_config_path())


class CanReceiverTests(unittest.TestCase):
    def test_can_payload_normalization_supports_float_scaling(self) -> None:
        message = can.Message(arbitration_id=0x123, data=struct.pack("<f", 12.5))
        payload = json.loads(
            can_message_to_plotter_payload(
                message, {"value_format": "float32_le", "scale": 2, "offset": -1}
            )
        )
        self.assertEqual(payload["id"], 0x23)
        self.assertEqual(payload["can_id"], 0x123)
        self.assertAlmostEqual(payload["value"], 24.0)

    def test_can_decoding_rejects_mismatched_or_unknown_formats(self) -> None:
        self.assertEqual(decode_can_value(b"\x34\x12", "uint_le"), 0x1234)
        with self.assertRaises(ValueError):
            decode_can_value(b"\x00\x00", "float32_le")
        with self.assertRaises(ValueError):
            decode_can_value(b"\x00", "decimal_text")

    def test_registry_uses_real_can_receiver(self) -> None:
        receiver = ReceiverRegistry().create_receiver(
            {
                "type": "CAN",
                "default": {"interface": "virtual", "channel": "plotter-tests"},
            }
        )
        self.assertIsInstance(receiver, CanReceiver)
        self.assertTrue(receiver.settings_valid())

    def test_can_is_configured_for_the_connection_dialog(self) -> None:
        config = json.loads((PROJECT_ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        can_definition = next(item for item in config["interfaces"] if item["type"] == "CAN")
        self.assertTrue(CanReceiver(can_definition["default"]).settings_valid())

        settings_qml = PROJECT_ROOT / "qml" / "content" / "ChartWindow" / "ConnectionManager" / "CanSettings.qml"
        self.assertTrue(settings_qml.is_file())
        dialog = (PROJECT_ROOT / "qml" / "content" / "Workbench" / "SourcesDialog.qml").read_text(encoding="utf-8")
        self.assertIn('CAN: "CanSettings.qml"', dialog)
        self.assertIn('"../ChartWindow/ConnectionManager/"', dialog)


class LegacyAdapterTests(unittest.TestCase):
    def test_all_legacy_connection_classes_are_concrete_adapters(self) -> None:
        adapters = (
            SerialConnection,
            MqttConnection,
            TelnetClientConnection,
            TelnetServerConnection,
            CanConnection,
        )
        for adapter in adapters:
            with self.subTest(adapter=adapter.__name__):
                self.assertFalse(inspect.isabstract(adapter))
                self.assertTrue(callable(getattr(adapter, "connect")))
                self.assertTrue(callable(getattr(adapter, "disconnect")))
                self.assertTrue(callable(getattr(adapter, "connected")))


class ChartFactoryTests(unittest.TestCase):
    def test_every_advertised_chart_has_an_existing_qml_renderer(self) -> None:
        expected_classes = {
            ChartType.XY_LINE: XYLineChart,
            ChartType.XY_SCATTER: XYScatterChart,
            ChartType.TIME_SERIES: TimeSeriesChart,
            ChartType.XYZ_SCATTER: XYZScatterChart,
        }
        for chart_type in ChartFactory.get_supported_types():
            with self.subTest(chart_type=chart_type):
                chart = ChartFactory.create_chart("test", "Test", chart_type)
                self.assertIsInstance(chart, expected_classes[chart_type])
                filename = Path(chart.get_qml_component()).name
                self.assertTrue((PROJECT_ROOT / "qml" / "content" / "ChartTypes" / filename).is_file())


class LoggerTests(unittest.TestCase):
    def test_console_output_formats_logging_arguments(self) -> None:
        logger = Logger.get_instance()
        logger.enabled = False
        logger.console_log = True
        output = io.StringIO()
        with redirect_stdout(output):
            log_info("Loaded %s item(s)", 4)
        self.assertIn("PYT - Loaded 4 item(s)", output.getvalue())


if __name__ == "__main__":
    unittest.main()

"""Regression coverage for the multi-window QML/backend data flow."""

from __future__ import annotations

import pytest
pytest.importorskip("PySide6", reason="Install requirements-dev.txt to run Qt integration tests")
pytest.importorskip("can", reason="python-can transport dependency missing")
pytest.importorskip("serial", reason="pyserial transport dependency missing")
pytest.importorskip("paho.mqtt.client", reason="paho-mqtt transport dependency missing")

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from PySide6.QtCore import QCoreApplication


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
QML_CONTENT = PROJECT_ROOT / "qml" / "content"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from Backend.backend import Backend, ConnectionInfo  # noqa: E402


class BackendConnectionCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self) -> None:
        Backend._Backend__backend_instance = None
        self.backend = Backend()
        self.backend._save_connections_to_config = Mock()

    def tearDown(self) -> None:
        self.backend._batch_timer.stop()
        self.backend._Backend__com_updater_timer.stop()
        Backend._Backend__backend_instance = None

    def test_delete_connection_clears_every_signal_state_and_notifies_qml(self) -> None:
        connection_id = "Serial_COM7_123"
        removed_id = f"{connection_id}_4"
        kept_id = "Serial_COM8_456_4"
        connections = self.backend._Backend__connections
        connections[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            interface_type="Serial",
            display_name="COM7",
            status="disconnected",
        )

        self.backend._graph_state.update({removed_id: {}, kept_id: {}})
        self.backend._point_buffer.update({removed_id: [(1, 2, 3, True)], kept_id: []})
        self.backend._point_buffer_3d.update({removed_id: [(1, 2, 3)], kept_id: []})
        self.backend._last_emit_time.update({removed_id: 1.0, kept_id: 2.0})
        self.backend._message_state.update({removed_id: {"uniqueId": removed_id}, kept_id: {}})
        self.backend._chart_line_overrides.update(
            {
                removed_id: {"display_name": "gone", "color": "#fff"},
                kept_id: {"display_name": "keep", "color": "#fff"},
            }
        )
        self.backend._dirty_messages.update({removed_id, kept_id})
        self.backend._ignored_signals.update({removed_id, kept_id})
        self.backend._pending_events = {
            "newGraph": [(removed_id, "gone", "#fff", "Serial"), (kept_id, "keep", "#fff", "Serial")],
            "append_graph_points_batch": [(removed_id, [[1, 2]]), (kept_id, [[3, 4]])],
        }

        self.assertTrue(self.backend.delete_connection(connection_id))

        for state in (
            self.backend._graph_state,
            self.backend._point_buffer,
            self.backend._point_buffer_3d,
            self.backend._last_emit_time,
            self.backend._message_state,
            self.backend._chart_line_overrides,
        ):
            self.assertNotIn(removed_id, state)
            self.assertIn(kept_id, state)
        self.assertNotIn(removed_id, self.backend._dirty_messages)
        self.assertIn(kept_id, self.backend._dirty_messages)
        self.assertNotIn(removed_id, self.backend._ignored_signals)
        self.assertIn(kept_id, self.backend._ignored_signals)

        queued_ids = [args[0] for args in self.backend._pending_events["newGraph"]]
        self.assertEqual(queued_ids, [kept_id])
        self.assertEqual(self.backend._pending_events["signals_removed"], [([removed_id],)])

    def test_line_metadata_can_be_set_before_first_data_point(self) -> None:
        unique_id = "Serial_COM7_123_4"

        self.assertTrue(self.backend.update_chart_line(unique_id, "Pressure", "#123456"))

        self.assertEqual(
            self.backend._chart_line_overrides[unique_id],
            {"display_name": "Pressure", "color": "#123456"},
        )
        self.assertNotIn(unique_id, self.backend._graph_state)

    def test_point_batches_cross_the_qml_boundary_as_indexable_lists(self) -> None:
        emitted: list[tuple] = []
        self.backend._queue_event = lambda *args: emitted.append(args)
        self.backend._point_buffer["Serial_1"] = [(1.0, 2.0, 3.0, True)]
        self.backend._point_buffer_3d["Serial_2"] = [(4.0, 5.0, 6.0)]

        self.backend._flush_points_for_line("Serial_1")
        self.backend._flush_points_for_line_3d("Serial_2")

        self.assertEqual(emitted[0][2], [[1.0, 2.0, 3.0, True]])
        self.assertEqual(emitted[1][2], [[4.0, 5.0, 6.0]])

    def test_configuration_export_uses_the_selected_file_and_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            default_path = temp_path / "config.json"
            export_path = temp_path / "exported.json"
            default_path.write_text(
                json.dumps(
                    {
                        "interfaces": [
                            {"type": "Test", "default": {"sample_ms": 50}}
                        ],
                        "qml": {"interfaces": ["Test"]},
                    }
                ),
                encoding="utf-8",
            )
            self.backend._Backend__config_path = str(default_path)
            self.backend.config(json.loads(default_path.read_text(encoding="utf-8")))
            self.backend._Backend__default_templates["Test"] = {"sample_ms": 125}
            self.backend._Backend__connections["Test_1_1"] = ConnectionInfo(
                connection_id="Test_1_1",
                interface_type="Test",
                display_name="Exported test source",
                status="disconnected",
                settings={"sample_ms": 125},
                created_at=1.0,
            )

            self.assertTrue(
                self.backend.save_configuration_to_file(export_path.as_uri())
            )

            exported = json.loads(export_path.read_text(encoding="utf-8"))
            self.assertEqual(exported["interfaces"][0]["default"]["sample_ms"], 125)
            self.assertEqual(
                exported["saved_connections"][0]["name"],
                "Exported test source",
            )

    def test_configuration_import_applies_and_persists_selected_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            default_path = temp_path / "config.json"
            import_path = temp_path / "import.json"
            initial = {
                "interfaces": [{"type": "Test", "default": {"sample_ms": 50}}],
                "qml": {"interfaces": ["Test"]},
            }
            imported = {
                "interfaces": [{"type": "Test", "default": {"sample_ms": 250}}],
                "qml": {"interfaces": ["Test"]},
                "saved_connections": [
                    {
                        "id": "Test_2_1",
                        "type": "Test",
                        "name": "Imported source",
                        "settings": {"sample_ms": 250},
                        "created_at": 2.0,
                    }
                ],
            }
            default_path.write_text(json.dumps(initial), encoding="utf-8")
            import_path.write_text(json.dumps(imported), encoding="utf-8")
            self.backend._Backend__config_path = str(default_path)
            self.backend.config(initial)

            self.assertTrue(
                self.backend.load_configuration_from_file(import_path.as_uri())
            )

            self.assertEqual(
                self.backend.get_default_template("Test")["sample_ms"], 250
            )
            self.assertEqual(
                [item["name"] for item in self.backend.get_connections()],
                ["Imported source"],
            )
            self.assertEqual(
                json.loads(default_path.read_text(encoding="utf-8")), imported
            )

    def test_invalid_configuration_import_does_not_replace_current_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            default_path = temp_path / "config.json"
            import_path = temp_path / "invalid.json"
            initial = {
                "interfaces": [{"type": "Test", "default": {"sample_ms": 50}}]
            }
            default_path.write_text(json.dumps(initial), encoding="utf-8")
            import_path.write_text(json.dumps({"interfaces": []}), encoding="utf-8")
            self.backend._Backend__config_path = str(default_path)
            self.backend.config(initial)

            self.assertFalse(
                self.backend.load_configuration_from_file(import_path.as_uri())
            )
            self.assertEqual(
                json.loads(default_path.read_text(encoding="utf-8")), initial
            )

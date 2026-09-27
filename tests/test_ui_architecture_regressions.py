"""Regression coverage for the multi-window QML/backend data flow."""

from __future__ import annotations

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

from Backend.backend import Backend, ConnectionInfo, _GraphBuffer  # noqa: E402


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
        self.backend._Backend__scroll_timer.stop()
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
        self.backend._Backend__graph_list.update(
            {removed_id: _GraphBuffer(), kept_id: _GraphBuffer()}
        )
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
            self.backend._Backend__graph_list,
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

    def test_legacy_disconnect_stops_the_active_connection_of_selected_type(self) -> None:
        receiver = Mock()
        self.backend._Backend__connections.update(
            {
                "Test_1_1": ConnectionInfo(
                    connection_id="Test_1_1",
                    interface_type="Test",
                    display_name="Inactive",
                    status="disconnected",
                    receiver=Mock(),
                ),
                "Test_2_2": ConnectionInfo(
                    connection_id="Test_2_2",
                    interface_type="Test",
                    display_name="Active",
                    status="connected",
                    receiver=receiver,
                ),
            }
        )

        self.assertTrue(self.backend.disconnectFrom("Test"))

        receiver.stop.assert_called_once_with()
        self.assertEqual(
            self.backend._Backend__connections["Test_2_2"].status,
            "disconnected",
        )

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


class QmlArchitectureContractTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        return (QML_CONTENT / relative_path).read_text(encoding="utf-8")

    def test_workspace_is_the_single_state_and_routing_owner(self) -> None:
        source = self._read("Workspace/WorkspaceController.qml")
        self.assertIn("property var chartLineModel: ChartLineModel", source)
        self.assertIn("property var chartModel: ListModel", source)
        self.assertIn("function createChart(", source)
        self.assertIn("function setSignalCharts(", source)
        self.assertIn("function routeGraphPointsBatch(", source)
        self.assertIn("events.append_graph_points_batch.connect(routeGraphPointsBatch)", source)

    def test_floating_window_is_only_a_window_and_renderer_host(self) -> None:
        source = self._read("FloatingWindows/FloatingChartWindow.qml")
        self.assertIn("property var workspaceController", source)
        self.assertIn("workspaceController.rendererReady", source)
        self.assertIn("workspaceController.removeChart", source)
        self.assertNotIn("property var _assignments", source)
        self.assertNotIn("WindowManager", source)

    def test_app_is_composition_only(self) -> None:
        source = self._read("App.qml")
        self.assertIn("WorkspaceController", source)
        self.assertNotIn("Qt.createComponent", source)
        self.assertNotIn("function routeGraphPointsBatch", source)
        self.assertNotIn("function findChartWindow", source)

    def test_app_ui_has_declarative_workspace_and_no_hidden_chart(self) -> None:
        source = self._read("AppUi.qml")
        workspace = self._read("Workspace/ChartWorkspace.qml")
        self.assertIn("ChartWorkspace", source)
        self.assertNotIn("ChartWindow {", source)
        self.assertIn("Repeater", workspace)
        self.assertIn("model: root.workspaceController.chartModel", workspace)

    def test_renderers_do_not_own_workspace_state_or_backend_subscriptions(self) -> None:
        for relative_path in (
            "ChartTypes/XYChartView.qml",
            "ChartTypes/XYChartRenderer.qml",
            "ChartTypes/TimeSeriesRenderer.qml",
            "ChartTypes/XYZChartRenderer.qml",
        ):
            source = self._read(relative_path)
            self.assertNotIn("chartLineModel", source, relative_path)
            self.assertNotIn("connectToBackend", source, relative_path)
            self.assertNotIn("_tryConnectBackendEvents", source, relative_path)
            self.assertNotIn("import Backend", source, relative_path)

    def test_workspace_routes_2d_and_3d_only_to_compatible_charts(self) -> None:
        source = self._read("Workspace/WorkspaceController.qml")
        two_d = source[
            source.index("function routeGraphPointsBatch(") : source.index("function routeGraphPoint3D(")
        ]
        three_d = source[
            source.index("function routeGraphPointsBatch3D(") : source.index("function _flushPendingForChart(")
        ]
        self.assertIn("_assignedChartIds(uniqueId, false)", two_d)
        self.assertIn("_assignedChartIds(uniqueId, true)", three_d)

    def test_window_state_is_persisted_by_workspace_model(self) -> None:
        controller = self._read("Workspace/WorkspaceController.qml")
        workspace = self._read("Workspace/ChartWorkspace.qml")
        floating = self._read("FloatingWindows/FloatingChartWindow.qml")
        self.assertIn("function updateChartWindowState(", controller)
        self.assertIn("minimized: false", controller)
        self.assertIn("isMinimized: model.minimized", workspace)
        self.assertIn("workspaceController.updateChartWindowState", floating)

    def test_xyz_renderer_reuses_compiled_point_components(self) -> None:
        source = self._read("ChartTypes/XYZChartRenderer.qml")
        self.assertIn("id: pointComponent", source)
        self.assertIn("pointComponent.createObject", source)
        self.assertIn("maxPointsPerSeries", source)
        self.assertNotIn("qrc:/qt/qml/QtQuick3D/Model", source)
        self.assertNotIn("Qt.createQmlObject", source)

    def test_grouped_lines_emit_line_keys(self) -> None:
        source = self._read("ChartWindow/ChartLinesList/ChartLinesListGrouped.qml")
        self.assertIn("root.lineVisibilityToggled(lineItem.lineKey", source)
        self.assertIn("root.lineSelected(lineItem.lineKey)", source)
        self.assertNotIn("root.lineVisibilityToggled(lineItem.uniqueId", source)

    def test_suspended_renderers_filter_unassigned_signals_before_buffering(self) -> None:
        xy = self._read("ChartTypes/XYChartRenderer.qml")
        time_series = self._read("ChartTypes/TimeSeriesRenderer.qml")
        xy_function = xy[xy.index("function appendPointsBatch") : xy.index("function clearLine")]
        time_function = time_series[
            time_series.index("function appendPointsBatch") : time_series.index("function removeLine")
        ]
        self.assertLess(xy_function.index("if(!series)"), xy_function.index("updatesSuspended"))
        self.assertLess(
            time_function.index("_getGraphsForUniqueId"),
            time_function.index("updatesSuspended"),
        )

    def test_settings_file_actions_call_the_selected_path_backend_api(self) -> None:
        source = self._read("Settings/Settings.qml")
        self.assertIn("Backend.save_configuration_to_file(fileUrl)", source)
        self.assertIn("Backend.load_configuration_from_file(fileUrl)", source)
        self.assertNotIn("placeholder for future implementation", source)

    def test_reusable_legacy_controls_have_action_handlers(self) -> None:
        controls = self._read("components/ControlsCard.qml")
        main_menu = self._read("MainMenu/MainMenu.qml")
        self.assertIn("controlsCard.appController.connect()", controls)
        self.assertIn("controlsCard.appController.disconnect()", controls)
        self.assertIn("newButton.onTriggered: newRequested()", main_menu)
        self.assertIn("closeButton.onTriggered: quitRequested()", main_menu)
        self.assertIn("settingsButton.onTriggered: settingsRequested()", main_menu)
        self.assertIn("aboutButton.onTriggered: aboutRequested()", main_menu)


if __name__ == "__main__":
    unittest.main()

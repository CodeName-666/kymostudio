"""Static source-contract checks; not a Qt/QML runtime test."""
import unittest
from pathlib import Path
QML_CONTENT = Path(__file__).resolve().parents[1] / "qml" / "content"

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
        self.assertIn("model: root.workspaceController ? root.workspaceController.chartModel : null", workspace)

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

    def test_suspended_renderers_filter_unassigned_signals_before_buffering(self) -> None:
        xy = self._read("ChartTypes/XYChartRenderer.qml")
        time_series = self._read("ChartTypes/TimeSeriesRenderer.qml")
        xy_function = xy[xy.index("function appendPointsBatch") : xy.index("function clearLine")]
        time_function = time_series[
            time_series.index("function appendPointsBatch") : time_series.index("function removeLine")
        ]
        self.assertLess(xy_function.index("if (!series || !points || !points.length)"), xy_function.index("updatesSuspended"))
        self.assertLess(
            time_function.index("_getGraphsForUniqueId"),
            time_function.index("updatesSuspended"),
        )

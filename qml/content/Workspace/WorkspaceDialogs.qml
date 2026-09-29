import QtQuick 6.4
import QtQuick.Controls 6.4
import "../ChartWindow/AddChartLineDialog"
import "../ChartWindow/EditChartLineDialog"

Item {
    id: root
    property var workspaceController: null

    function openAddSignal() {
        addSignalDialog.refreshConnectionsList(
            workspaceController ? workspaceController.getAvailableConnections() : [],
            workspaceController ? workspaceController.getUsedDataIds() : []
        )
        addSignalDialog.open()
    }

    function openEditLine(lineKey) {
        if (!workspaceController) return
        var line = workspaceController.chartLineModel.getLineByKey(lineKey)
        if (!line) return
        editLineDialog.loadChartLine(
            line.lineKey,
            line.uniqueId,
            line.displayName,
            line.color,
            line.interfaceType,
            line.dataId,
            line.chartTitle
        )
        editLineDialog.open()
    }

    AddChartLineDialog {
        id: addSignalDialog
        parent: Overlay.overlay
        anchors.centerIn: parent

        onAboutToShow: {
            refreshConnectionsList(
                root.workspaceController ? root.workspaceController.getAvailableConnections() : [],
                root.workspaceController ? root.workspaceController.getUsedDataIds() : []
            )
        }

        onChartLineAdded: function(uniqueId, displayName, lineColor, connectionId, dataId, interfaceSettings) {
            if (!root.workspaceController) return
            var backend = root.workspaceController.backendInterface
            var details = backend && backend.get_connection_details ? backend.get_connection_details(connectionId) : null
            root.workspaceController.addSignal(
                uniqueId,
                displayName,
                lineColor,
                details ? details.type : "Unknown",
                dataId,
                interfaceSettings
            )
        }
    }

    EditChartLineDialog {
        id: editLineDialog
        parent: Overlay.overlay
        anchors.centerIn: parent

        onChartLineUpdated: function(lineKey, displayName, lineColor) {
            if (root.workspaceController) root.workspaceController.updateSignal(lineKey, displayName, lineColor)
        }

        onChartLineDeleted: function(lineKey) {
            if (root.workspaceController) root.workspaceController.removeChartLine(lineKey)
        }
    }
}

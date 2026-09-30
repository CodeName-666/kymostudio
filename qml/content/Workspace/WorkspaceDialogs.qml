import QtQuick 6.4
import QtQuick.Controls 6.4
import "../Workbench"

Item {
    id: root
    property var workspaceController: null

    function openAddSignal() { signalDialog.open() }

    SignalDialog {
        id: signalDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        workspaceController: root.workspaceController

        onSignalRequested: function(uniqueId, displayName, lineColor, connectionId, dataId) {
            if (!root.workspaceController) return
            var backend = root.workspaceController.backendInterface
            var details = backend && backend.get_connection_details ? backend.get_connection_details(connectionId) : null
            root.workspaceController.addSignal(uniqueId, displayName, lineColor, details ? details.type : "Unknown", dataId, {})
        }
    }
}

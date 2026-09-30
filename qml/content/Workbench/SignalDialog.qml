import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/**
 * Creates a signal ahead of its first data packet (source + data ID, name, colour).
 * Signals with unknown IDs are also created automatically when data arrives.
 */
WorkbenchDialog {
    id: root
    property var workspaceController
    property var connections: []
    signal signalRequested(string uniqueId, string displayName, string lineColor, string connectionId, int dataId)

    title: qsTr("Signal anlegen")
    width: 520

    readonly property var connection: sourceCombo.currentIndex >= 0 ? connections[sourceCombo.currentIndex] : null
    readonly property string uniqueId: connection ? connection.id + "_" + dataIdBox.value : ""
    readonly property var existing: uniqueId && workspaceController && workspaceController.signalModel.count >= 0
        ? workspaceController.signalModel.getSignal(uniqueId) : null
    readonly property bool valid: !!connection && !existing

    function typeLabel(type) {
        return ({ Serial: qsTr("Seriell"), Telnet: qsTr("TCP"), MQTT: "MQTT", CAN: "CAN", Test: qsTr("Test") })[type] || type
    }
    function isUsed(connectionId, dataId) {
        return !!workspaceController.signalModel.getSignal(connectionId + "_" + dataId)
    }
    function suggest() {
        if (!connection) return
        var id = 0
        while (id < 255 && isUsed(connection.id, id)) id++
        dataIdBox.value = id
        nameField.text = ""
    }

    onAboutToShow: {
        connections = workspaceController ? workspaceController.getAvailableConnections() : []
        sourceCombo.currentIndex = connections.length ? 0 : -1
        var count = workspaceController ? workspaceController.signalModel.count : 0
        swatches.color = AppTheme.seriesColors[count % AppTheme.seriesColors.length]
        suggest()
    }
    onAccepted: {
        if (!valid) return
        var name = nameField.text.trim() || nameField.placeholderText
        signalRequested(uniqueId, name, swatches.color.toString(), connection.id, dataIdBox.value)
    }

    contentItem: ColumnLayout {
        spacing: 14

        Label {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.topMargin: 16
            wrapMode: Text.WordWrap
            color: AppTheme.text.hint
            font.pixelSize: AppTheme.fontSize.small
            text: qsTr("Unbekannte Daten-IDs erscheinen beim ersten Paket automatisch. Hier legst du ein Signal vorab mit Namen und Farbe an.")
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            spacing: 10

            FieldRow {
                label: qsTr("Quelle")
                labelWidth: 88
                required: true
                ComboBox {
                    id: sourceCombo
                    Layout.fillWidth: true
                    Layout.maximumWidth: 300
                    enabled: root.connections.length > 0
                    model: root.connections.map(function(c) { return c.name + " · " + root.typeLabel(c.type) })
                    displayText: root.connections.length ? currentText : qsTr("Keine Quelle angelegt")
                    onActivated: root.suggest()
                    Accessible.name: qsTr("Quelle")
                }
            }
            FieldRow {
                label: qsTr("Daten-ID")
                labelWidth: 88
                required: true
                SpinBox { id: dataIdBox; from: 0; to: 255; editable: true; Layout.preferredWidth: 110; Accessible.name: qsTr("Daten-ID") }
                Row {
                    spacing: 6
                    Layout.alignment: Qt.AlignVCenter
                    Icon {
                        name: root.existing ? "warning" : "check"; size: 14
                        color: root.existing ? AppTheme.palette.warning : AppTheme.palette.success
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Label {
                        text: root.existing ? qsTr("belegt durch „%1“").arg(root.existing.displayName) : qsTr("frei")
                        color: root.existing ? AppTheme.tone.warning.text : AppTheme.text.hint
                        font.pixelSize: AppTheme.fontSize.small
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
            FieldRow {
                label: qsTr("Name")
                labelWidth: 88
                TextField {
                    id: nameField
                    Layout.fillWidth: true
                    Layout.maximumWidth: 300
                    placeholderText: root.connection ? qsTr("%1 · ID %2").arg(root.connection.name).arg(dataIdBox.value) : ""
                    maximumLength: 100
                    selectByMouse: true
                    Accessible.name: qsTr("Signalname")
                    onAccepted: if (root.valid) root.accept()
                }
            }
            FieldRow {
                label: qsTr("Farbe")
                labelWidth: 88
                ColorSwatches { id: swatches }
            }
        }
        Item { implicitHeight: 6 }
    }

    footer: DialogFooter {
        Item { Layout.fillWidth: true }
        UiButton { text: qsTr("Abbrechen"); onClicked: root.reject() }
        UiButton { text: qsTr("Anlegen"); iconName: "plus"; variant: "primary"; enabled: root.valid; onClicked: root.accept() }
    }
}

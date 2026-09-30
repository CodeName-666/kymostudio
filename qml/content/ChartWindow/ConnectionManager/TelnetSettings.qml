import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0
import "../../Workbench"

/** TCP (Telnet) source settings. Keys: mode, port, and for clients host, reconnect_delay. */
ColumnLayout {
    id: root
    spacing: 20

    readonly property var modes: ["Client", "Server"]
    readonly property bool client: modeSeg.currentIndex === 0

    FormSection {
        title: qsTr("Verbindung")
        FieldRow {
            label: qsTr("Modus")
            required: true
            hint: root.client ? qsTr("Verbindet sich mit einem entfernten Server.") : qsTr("Wartet an diesem Port auf eingehende Verbindungen.")
            Segmented { id: modeSeg; accessibleName: qsTr("Modus"); options: [{ text: "Client" }, { text: "Server" }]; currentIndex: 0 }
        }
        FieldRow {
            visible: root.client
            label: qsTr("Host")
            required: true
            TextField {
                id: hostField
                text: "localhost"
                Layout.preferredWidth: 240
                placeholderText: qsTr("localhost oder 192.168.1.100")
                selectByMouse: true
                Accessible.name: qsTr("Host")
            }
        }
        FieldRow {
            label: qsTr("Port")
            required: true
            TextField {
                id: portField
                text: "23"
                Layout.preferredWidth: 90
                placeholderText: "23"
                validator: IntValidator { bottom: 1; top: 65535 }
                selectByMouse: true
                Accessible.name: qsTr("Port")
            }
        }
        FieldRow {
            visible: root.client
            label: qsTr("Neuverbindung")
            hint: qsTr("Wartezeit nach Verbindungsabbruch; 0 = keine automatische Neuverbindung.")
            SpinBox { id: reconnectSpinBox; from: 0; to: 60; value: 5; editable: true; Layout.preferredWidth: 110; Accessible.name: qsTr("Neuverbindung nach Sekunden") }
            Label { text: qsTr("s"); color: AppTheme.text.hint }
        }
    }

    function loadDefaults(defaults) {
        if (defaults.mode && modes.indexOf(defaults.mode) >= 0) modeSeg.currentIndex = modes.indexOf(defaults.mode)
        if (defaults.host) hostField.text = defaults.host
        if (defaults.port) portField.text = defaults.port.toString()
        if (defaults.reconnect_delay !== undefined) reconnectSpinBox.value = defaults.reconnect_delay
    }

    function getSettings() {
        var settings = { "mode": modes[modeSeg.currentIndex], "port": parseInt(portField.text) }
        if (client) {
            settings.host = hostField.text
            settings.reconnect_delay = reconnectSpinBox.value
        }
        return settings
    }
}

import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15
import Common 1.0
import Theme 1.0

ColumnLayout {
    id: root

    spacing: 12

    // Mode Selection
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Modus") + " *"
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        ComboBox {
            id: modeCombo
            Layout.fillWidth: true
            font.pixelSize: 12

            model: ["Client", "Server"]
            currentIndex: 0

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: Text {
                text: modeCombo.displayText
                font: modeCombo.font
                color: AppTheme.text.primary
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
            }
        }

        Label {
            text: qsTr("Client: mit entferntem Server verbinden\nServer: eingehende Verbindungen annehmen")
            font.pixelSize: 10
            color: "#808080"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }

    // Host (only for Client mode)
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6
        visible: modeCombo.currentText === "Client"

        Label {
            text: qsTr("Host") + " *"
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        TextField {
            id: hostField
            Layout.fillWidth: true
            placeholderText: qsTr("z. B. localhost oder 192.168.1.100")
            text: "localhost"
            font.pixelSize: 12

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            color: AppTheme.text.primary
        }
    }

    // Port
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Port") + " *"
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        TextField {
            id: portField
            Layout.fillWidth: true
            placeholderText: qsTr("Standard: 23")
            text: "23"
            font.pixelSize: 12
            validator: IntValidator { bottom: 1; top: 65535 }

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            color: AppTheme.text.primary
        }
    }

    // Reconnect Delay (only for Client mode)
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6
        visible: modeCombo.currentText === "Client"

        Label {
            text: qsTr("Neuverbindung nach (Sekunden)")
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        SpinBox {
            id: reconnectSpinBox
            Layout.fillWidth: true
            from: 0
            to: 60
            value: 5
            editable: true
            font.pixelSize: 12

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: TextInput {
                text: reconnectSpinBox.textFromValue(reconnectSpinBox.value, reconnectSpinBox.locale)
                font: reconnectSpinBox.font
                color: AppTheme.text.primary
                horizontalAlignment: Qt.AlignHCenter
                verticalAlignment: Qt.AlignVCenter
                readOnly: !reconnectSpinBox.editable
                validator: reconnectSpinBox.validator
            }

            up.indicator: Rectangle {
                x: reconnectSpinBox.width - width
                height: parent.height / 2
                color: reconnectSpinBox.up.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "+"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }

            down.indicator: Rectangle {
                x: reconnectSpinBox.width - width
                y: parent.height / 2
                height: parent.height / 2
                color: reconnectSpinBox.down.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "-"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }
        }

        Label {
            text: qsTr("0 = keine automatische Neuverbindung")
            font.pixelSize: 10
            color: "#808080"
        }
    }

    Item {
        Layout.fillHeight: true
    }

    // Functions
    function loadDefaults(defaults) {
        if(defaults.mode) {
            var modeIndex = modeCombo.model.indexOf(defaults.mode)
            if(modeIndex >= 0) {
                modeCombo.currentIndex = modeIndex
            }
        }
        if(defaults.host) hostField.text = defaults.host
        if(defaults.port) portField.text = defaults.port.toString()
        if(defaults.reconnect_delay !== undefined) {
            reconnectSpinBox.value = defaults.reconnect_delay
        }
    }

    function getSettings() {
        var settings = {
            "mode": modeCombo.currentText,
            "port": parseInt(portField.text)
        }

        if(modeCombo.currentText === "Client") {
            settings.host = hostField.text
            settings.reconnect_delay = reconnectSpinBox.value
        }

        return settings
    }
}

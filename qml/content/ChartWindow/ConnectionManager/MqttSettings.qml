import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15
import Common 1.0
import Theme 1.0

ScrollView {
    id: root

    clip: true
    contentWidth: availableWidth

    ColumnLayout {
        width: root.availableWidth
        spacing: 12

        // Host
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

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
                placeholderText: qsTr("Standard: 1883")
                text: "1883"
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

        // RX Topic
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: qsTr("Empfangs-Topic") + " *"
                font.pixelSize: 12
                font.bold: true
                color: AppTheme.text.primary
            }

            TextField {
                id: rxTopicField
                Layout.fillWidth: true
                placeholderText: qsTr("z. B. sensor/data")
                text: "sensor/data"
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

        // TX Topic
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: qsTr("Sende-Topic")
                font.pixelSize: 12
                font.bold: true
                color: AppTheme.text.primary
            }

            TextField {
                id: txTopicField
                Layout.fillWidth: true
                placeholderText: qsTr("z. B. sensor/command")
                text: "sensor/command"
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

        // Client ID
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: qsTr("Client-ID")
                font.pixelSize: 12
                font.bold: true
                color: AppTheme.text.primary
            }

            TextField {
                id: clientIdField
                Layout.fillWidth: true
                placeholderText: qsTr("Leer lassen für automatische Vergabe")
                font.pixelSize: 12

                background: Rectangle {
                    color: AppTheme.inputs.background
                    border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                    border.width: 1
                    radius: 4
                }

                color: AppTheme.text.primary
            }

            Label {
                text: qsTr("Wird automatisch vergeben, wenn leer")
                font.pixelSize: 10
                color: "#808080"
            }
        }

        // Username
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: qsTr("Benutzername (optional)")
                font.pixelSize: 12
                font.bold: true
                color: AppTheme.text.primary
            }

            TextField {
                id: usernameField
                Layout.fillWidth: true
                placeholderText: qsTr("Leer lassen ohne Anmeldung")
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

        // Password
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: qsTr("Passwort (optional)")
                font.pixelSize: 12
                font.bold: true
                color: AppTheme.text.primary
            }

            TextField {
                id: passwordField
                Layout.fillWidth: true
                placeholderText: qsTr("Leer lassen ohne Anmeldung")
                echoMode: TextInput.Password
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

        Item {
            Layout.fillHeight: true
        }
    }

    // Functions
    function loadDefaults(defaults) {
        if(defaults.host) hostField.text = defaults.host
        if(defaults.port) portField.text = defaults.port.toString()
        if(defaults.rx_topic) rxTopicField.text = defaults.rx_topic
        if(defaults.tx_topic) txTopicField.text = defaults.tx_topic
        if(defaults.client_id) clientIdField.text = defaults.client_id
        if(defaults.username) usernameField.text = defaults.username
        if(defaults.password) passwordField.text = defaults.password
    }

    function getSettings() {
        return {
            "host": hostField.text,
            "port": parseInt(portField.text),
            "rx_topic": rxTopicField.text,
            "tx_topic": txTopicField.text,
            "client_id": clientIdField.text,
            "username": usernameField.text,
            "password": passwordField.text
        }
    }
}

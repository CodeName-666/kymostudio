// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0
import "../../Workbench"

/** MQTT source settings. Keys: host, port, rx_topic, tx_topic, client_id, username, password. */
ColumnLayout {
    id: root
    spacing: 20

    FormSection {
        title: qsTr("Broker")
        FieldRow {
            label: qsTr("Host")
            required: true
            TextField { id: hostField; Layout.preferredWidth: 240; text: "localhost"; placeholderText: qsTr("localhost oder 192.168.1.100"); selectByMouse: true; Accessible.name: qsTr("Host") }
        }
        FieldRow {
            label: qsTr("Port")
            required: true
            TextField { id: portField; Layout.preferredWidth: 90; text: "1883"; placeholderText: "1883"; selectByMouse: true; Accessible.name: qsTr("Port"); validator: IntValidator { bottom: 1; top: 65535 } }
        }
    }

    FormSection {
        title: qsTr("Topics")
        FieldRow {
            label: qsTr("Empfangen")
            required: true
            TextField { id: rxTopicField; Layout.preferredWidth: 280; text: "sensor/data"; placeholderText: qsTr("z. B. sensor/data"); selectByMouse: true; Accessible.name: qsTr("Empfangs-Topic") }
        }
        FieldRow {
            label: qsTr("Senden")
            hint: qsTr("Optional, nur für Befehle an das Gerät.")
            TextField { id: txTopicField; Layout.preferredWidth: 280; text: "sensor/command"; placeholderText: qsTr("z. B. sensor/command"); selectByMouse: true; Accessible.name: qsTr("Sende-Topic") }
        }
    }

    FormSection {
        title: qsTr("Anmeldung · optional")
        FieldRow {
            label: qsTr("Client-ID")
            TextField { id: clientIdField; Layout.preferredWidth: 200; placeholderText: qsTr("automatisch"); selectByMouse: true; Accessible.name: qsTr("Client-ID") }
        }
        FieldRow {
            label: qsTr("Benutzer")
            TextField { id: usernameField; Layout.preferredWidth: 200; placeholderText: qsTr("ohne Anmeldung"); selectByMouse: true; Accessible.name: qsTr("Benutzername") }
        }
        FieldRow {
            label: qsTr("Passwort")
            TextField { id: passwordField; Layout.preferredWidth: 200; placeholderText: qsTr("ohne Anmeldung"); echoMode: TextInput.Password; Accessible.name: qsTr("Passwort") }
        }
    }

    function loadDefaults(defaults) {
        if (defaults.host) hostField.text = defaults.host
        if (defaults.port) portField.text = defaults.port.toString()
        if (defaults.rx_topic) rxTopicField.text = defaults.rx_topic
        if (defaults.tx_topic) txTopicField.text = defaults.tx_topic
        if (defaults.client_id) clientIdField.text = defaults.client_id
        if (defaults.username) usernameField.text = defaults.username
        if (defaults.password) passwordField.text = defaults.password
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

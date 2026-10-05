// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/** Data sources: list on the left, settings of the selected or new source on the right. */
WorkbenchDialog {
    id: root
    property var backend
    property string selectedId: ""
    property bool creating: false
    property string typeName: ""
    property string status: ""
    property var errors: ({})
    property string formError: ""
    property var interfaceTypes: []

    title: qsTr("Quellen")
    width: Math.min(1000, parent ? parent.width - 64 : 1000)
    height: Math.min(680, parent ? parent.height - 64 : 680)

    readonly property var typeLabels: ({ Serial: qsTr("Seriell"), Telnet: qsTr("TCP"), MQTT: "MQTT", CAN: "CAN", Test: qsTr("Test") })
    readonly property var forms: ({ Serial: "SerialSettings.qml", MQTT: "MqttSettings.qml", Telnet: "TelnetSettings.qml", CAN: "CanSettings.qml", Test: "TestSettings.qml" })

    function openFor(connectionId) {
        open()
        if (connectionId) select(connectionId)
    }
    function openNew() {
        open()
        startNew()
    }
    function refresh() {
        interfaceTypes = backend.get_interface_types()
        var list = backend.get_connections()
        connections.clear()
        for (var i = 0; i < list.length; i++)
            connections.append({ connectionId: list[i].id, name: list[i].name, type: list[i].type, status: list[i].status })
        if (!creating && !selectedId && connections.count) select(connections.get(0).connectionId)
        if (!creating && !connections.count) startNew()
    }
    function loadForm(type, settings) {
        formLoader.source = forms[type] ? Qt.resolvedUrl("../ChartWindow/ConnectionManager/" + forms[type]) : ""
        if (formLoader.item && formLoader.item.loadDefaults) formLoader.item.loadDefaults(settings || {})
    }
    function select(connectionId) {
        var details = backend.get_connection_details(connectionId)
        if (!details || !details.id) return
        creating = false
        formError = ""
        selectedId = details.id
        typeName = details.type
        status = details.status
        nameField.text = details.name
        loadForm(details.type, details.settings)
    }
    function startNew(type) {
        creating = true
        formError = ""
        selectedId = ""
        status = ""
        nameField.text = ""
        var types = interfaceTypes
        var chosen = null
        for (var i = 0; i < types.length; i++) if (types[i].type === (type || "Serial")) chosen = types[i]
        if (!chosen && types.length) chosen = types[0]
        typeName = chosen ? chosen.type : ""
        loadForm(typeName, chosen ? chosen.defaults : {})
    }
    function save(connectAfter) {
        formError = ""
        var settings = formLoader.item && formLoader.item.getSettings ? formLoader.item.getSettings() : {}
        var name = nameField.text.trim()
        if (creating) {
            var id = backend.create_connection(typeName, name, settings)
            if (!id) { formError = formError || qsTr("Quelle nicht angelegt. Pflichtfelder und Werte prüfen."); return }
            creating = false
            refresh()
            select(id)
            if (connectAfter) backend.start_connection(id)
            return
        }
        if (!backend.update_connection_settings(selectedId, settings) || (name && !backend.rename_connection(selectedId, name))) {
            formError = formError || qsTr("Änderungen nicht gespeichert. Werte prüfen.")
            return
        }
        refresh()
        if (connectAfter) backend.start_connection(selectedId)
    }
    function statusText(value) {
        return value === "connected" ? qsTr("verbunden") : value === "connecting" ? qsTr("verbindet …")
            : value === "error" ? qsTr("Fehler") : qsTr("getrennt")
    }
    function statusColor(value) {
        return value === "connected" ? AppTheme.palette.success : value === "connecting" ? AppTheme.palette.warning
            : value === "error" ? AppTheme.palette.danger : AppTheme.palette.idle
    }

    onAboutToShow: refresh()
    onClosed: { creating = false; selectedId = "" }

    ListModel { id: connections }
    Connections {
        target: root.backend
        ignoreUnknownSignals: true
        function onConnections_changed() { if (root.opened) root.refresh() }
        function onConnection_status_changed(connectionId, status, details) {
            if (details && details.error) {
                var next = Object.assign({}, root.errors)
                next[connectionId] = details.error
                root.errors = next
            }
            for (var i = 0; i < connections.count; i++)
                if (connections.get(i).connectionId === connectionId) connections.setProperty(i, "status", status)
            if (connectionId === root.selectedId) root.status = status
        }
        function onStatus_message(level, message) {
            if (root.opened && level === "error") root.formError = message
        }
    }

    contentItem: RowLayout {
        spacing: 0

        // Source list
        ColumnLayout {
            Layout.preferredWidth: 280
            Layout.fillHeight: true
            Layout.margins: 10
            spacing: 4
            ListView {
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 2
                model: connections
                delegate: ItemDelegate {
                    id: entry
                    required property string connectionId
                    required property string name
                    required property string type
                    required property string status
                    width: list.width
                    height: 52
                    highlighted: !root.creating && root.selectedId === connectionId
                    onClicked: root.select(connectionId)
                    Accessible.name: name + ", " + root.statusText(status)
                    background: Rectangle {
                        radius: AppTheme.radius.medium
                        color: entry.highlighted ? AppTheme.palette.primarySoft : entry.hovered ? AppTheme.surfaces.hover : "transparent"
                        border.color: entry.visualFocus ? AppTheme.borders.focus : entry.highlighted ? AppTheme.palette.primaryBorder : "transparent"
                    }
                    contentItem: RowLayout {
                        spacing: 10
                        Rectangle { width: 8; height: 8; radius: 4; color: root.statusColor(entry.status) }
                        ColumnLayout {
                            spacing: 0
                            Layout.fillWidth: true
                            Label { text: entry.name; font.weight: Font.Medium; elide: Text.ElideRight; Layout.fillWidth: true }
                            Label {
                                text: (root.typeLabels[entry.type] || entry.type) + " · " + root.statusText(entry.status)
                                font.pixelSize: AppTheme.fontSize.small
                                color: entry.status === "error" ? "#F29C99" : AppTheme.text.hint
                            }
                        }
                    }
                }
            }
            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: AppTheme.borders.primary }
            UiButton {
                Layout.fillWidth: true
                Layout.topMargin: 6
                text: qsTr("Neue Quelle")
                iconName: "plus"
                variant: root.creating ? "primary" : "neutral"
                onClicked: root.startNew()
            }
        }
        Rectangle { Layout.fillHeight: true; implicitWidth: 1; color: AppTheme.borders.primary }

        // Settings of the selected source
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            ScrollView {
                id: formScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth

                ColumnLayout {
                    x: 24
                    width: Math.min(640, formScroll.availableWidth - 48)
                    spacing: 20

                    Item { implicitHeight: 2 }

                    Rectangle {
                        readonly property string message: root.formError || (root.status === "error" ? (root.errors[root.selectedId] || qsTr("Verbindung fehlgeschlagen.")) : "")
                        visible: message !== ""
                        Layout.fillWidth: true
                        implicitHeight: errorRow.implicitHeight + 20
                        radius: AppTheme.radius.large
                        color: AppTheme.tone.danger.bg
                        border.color: AppTheme.tone.danger.border
                        Accessible.role: Accessible.AlertMessage
                        Accessible.name: message
                        RowLayout {
                            id: errorRow
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            Icon { name: "error"; color: AppTheme.tone.danger.text; Layout.alignment: Qt.AlignTop }
                            Label { text: parent.parent.message; color: AppTheme.tone.danger.text; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        }
                    }

                    // New source: pick the type first.
                    FormSection {
                        visible: root.creating
                        title: qsTr("Art der Quelle")
                        SourceTypePicker {
                            id: typePicker
                            Layout.fillWidth: true
                            types: root.interfaceTypes
                            current: root.typeName
                            onChosen: function(type) { root.startNew(type) }
                        }
                    }

                    // Existing source: type and live status at a glance.
                    RowLayout {
                        visible: !root.creating
                        spacing: 10
                        Rectangle {
                            implicitWidth: typeBadge.implicitWidth + 20
                            implicitHeight: 26
                            radius: 13
                            color: AppTheme.surfaces.control
                            border.color: AppTheme.borders.strong
                            Row {
                                id: typeBadge
                                anchors.centerIn: parent
                                spacing: 6
                                Icon { name: typePicker.iconFor(root.typeName); size: 14; color: AppTheme.text.secondary; anchors.verticalCenter: parent.verticalCenter }
                                Label { text: typePicker.label(root.typeName); font.pixelSize: AppTheme.fontSize.small; anchors.verticalCenter: parent.verticalCenter }
                            }
                        }
                        Rectangle { width: 8; height: 8; radius: 4; color: root.statusColor(root.status) }
                        Label { text: root.statusText(root.status); color: AppTheme.text.secondary }
                        Label {
                            text: qsTr("· Änderungen starten eine laufende Quelle neu.")
                            color: AppTheme.text.hint
                            font.pixelSize: AppTheme.fontSize.small
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    FormSection {
                        title: qsTr("Allgemein")
                        FieldRow {
                            label: qsTr("Name")
                            hint: root.creating ? qsTr("Leer lassen für einen automatischen Namen.") : ""
                            TextField {
                                id: nameField
                                Layout.preferredWidth: 280
                                placeholderText: root.typeLabels[root.typeName] || qsTr("Name der Quelle")
                                Accessible.name: qsTr("Name der Quelle")
                                selectByMouse: true
                                maximumLength: 100
                            }
                        }
                    }

                    Loader { id: formLoader; Layout.fillWidth: true }

                    Item { implicitHeight: 12 }
                }
            }

            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: AppTheme.borders.primary }
            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 12
                Layout.leftMargin: 20
                spacing: 8
                UiButton { visible: !root.creating; text: qsTr("Quelle löschen"); iconName: "trash"; variant: "danger"; onClicked: deleteConfirm.open() }
                Item { Layout.fillWidth: true }
                UiButton {
                    visible: !root.creating && (root.status === "connected" || root.status === "connecting")
                    text: qsTr("Trennen"); iconName: "stop"
                    onClicked: root.backend.stop_connection(root.selectedId)
                }
                UiButton { text: qsTr("Speichern"); enabled: !!formLoader.item; onClicked: root.save(false) }
                UiButton {
                    text: root.creating ? qsTr("Anlegen & verbinden") : qsTr("Speichern & verbinden")
                    variant: "primary"
                    enabled: !!formLoader.item
                    onClicked: root.save(true)
                }
            }
        }
    }

    ConfirmDialog {
        id: deleteConfirm
        title: qsTr("Quelle löschen?")
        text: qsTr("„%1“ wird gestoppt und gelöscht. Ihre Signale verschwinden aus allen Diagrammen, die Rohwerte werden verworfen.").arg(nameField.text)
        onAccepted: {
            if (root.backend.delete_connection(root.selectedId)) {
                root.selectedId = ""
                root.refresh()
            }
        }
    }
}

// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/** Row of source-type tiles (icon, name, one-line purpose). `types`: [{type}] from the backend. */
RowLayout {
    id: root
    property var types: []
    property string current: ""
    signal chosen(string type)
    spacing: 8

    readonly property var meta: ({
        Serial: { name: qsTr("Seriell"), sub: qsTr("UART · COM-Port"), icon: "plug" },
        Telnet: { name: qsTr("TCP"), sub: qsTr("Client · Server"), icon: "network" },
        MQTT: { name: "MQTT", sub: qsTr("Broker · Topic"), icon: "broadcast" },
        CAN: { name: "CAN", sub: qsTr("Bus-Adapter"), icon: "bus" },
        Test: { name: qsTr("Test"), sub: qsTr("Signalgenerator"), icon: "wave" }
    })
    function label(type) { return meta[type] ? meta[type].name : type }
    function iconFor(type) { return meta[type] ? meta[type].icon : "plug" }

    Repeater {
        model: root.types
        delegate: AbstractButton {
            id: tile
            required property var modelData
            readonly property var info: root.meta[modelData.type] || { name: modelData.type, sub: "", icon: "plug" }
            readonly property bool selected: root.current === modelData.type
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.maximumWidth: 150
            implicitHeight: 56
            checkable: true
            checked: selected
            hoverEnabled: true
            focusPolicy: Qt.StrongFocus
            Accessible.role: Accessible.RadioButton
            Accessible.name: info.name + ", " + info.sub
            onClicked: root.chosen(modelData.type)
            background: Rectangle {
                radius: AppTheme.radius.large
                color: tile.selected ? AppTheme.palette.primarySoft : tile.hovered ? AppTheme.surfaces.hover : AppTheme.surfaces.panel
                border.width: tile.visualFocus ? 2 : 1
                border.color: tile.visualFocus || tile.selected ? AppTheme.palette.primary : AppTheme.borders.primary
            }
            contentItem: RowLayout {
                spacing: 8
                Icon { name: tile.info.icon; color: tile.selected ? AppTheme.palette.primary : AppTheme.text.secondary; Layout.leftMargin: 10 }
                ColumnLayout {
                    spacing: 1
                    Layout.fillWidth: true
                    Label { text: tile.info.name; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                    Label { text: tile.info.sub; font.pixelSize: AppTheme.fontSize.caption; color: AppTheme.text.hint; elide: Text.ElideRight; Layout.fillWidth: true }
                }
            }
        }
    }
}

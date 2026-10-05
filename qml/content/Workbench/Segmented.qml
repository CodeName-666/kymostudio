// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import Theme 1.0

/**
 * Segmented toggle. `options`: [{text, icon?, tone?}] where tone "warning" tints
 * the selected segment. Emits activated(index) on user choice only.
 */
Rectangle {
    id: root
    property var options: []
    property int currentIndex: 0
    property string accessibleName: ""
    signal activated(int index)

    implicitWidth: row.implicitWidth + 4
    implicitHeight: 28
    radius: 7
    color: AppTheme.surfaces.background
    border.color: AppTheme.borders.primary
    Accessible.role: Accessible.Grouping
    Accessible.name: accessibleName

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 2
        Repeater {
            model: root.options
            delegate: AbstractButton {
                id: segment
                required property var modelData
                required property int index
                readonly property bool selected: index === root.currentIndex
                readonly property bool warn: selected && modelData.tone === "warning"
                readonly property color fg: warn ? "#F5CF83" : selected ? AppTheme.text.primary : hovered ? AppTheme.text.primary : AppTheme.text.secondary
                enabled: root.enabled && modelData.enabled !== false
                height: 24
                implicitWidth: content.implicitWidth + 20
                hoverEnabled: true
                focusPolicy: Qt.StrongFocus
                checkable: true
                checked: selected
                text: modelData.text
                Accessible.name: modelData.text
                opacity: enabled ? 1 : 0.45
                onClicked: { root.currentIndex = index; root.activated(index) }
                contentItem: Item {
                    Row {
                        id: content
                        anchors.centerIn: parent
                        spacing: 6
                        Icon { visible: !!segment.modelData.icon; name: segment.modelData.icon || ""; size: 14; color: segment.fg; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: segment.modelData.text; color: segment.fg; font.family: AppTheme.fontFamily; font.pixelSize: AppTheme.fontSize.small; font.weight: Font.Medium; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
                background: Rectangle {
                    radius: 5
                    color: segment.warn ? "#3A2E14" : segment.selected ? AppTheme.borders.primary : "transparent"
                    border.width: segment.visualFocus ? 2 : 0
                    border.color: AppTheme.borders.focus
                }
            }
        }
    }
}

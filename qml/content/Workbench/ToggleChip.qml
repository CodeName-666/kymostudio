// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import Theme 1.0

/** Small checkable pill, e.g. for assigning a signal to a chart axis. */
AbstractButton {
    id: control
    property bool mono: true
    readonly property color fg: checked ? "#8FD0F6" : hovered ? AppTheme.text.primary : AppTheme.text.secondary
    checkable: true
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    implicitHeight: 24
    implicitWidth: row.implicitWidth + 16
    opacity: enabled ? 1 : 0.4
    Accessible.role: Accessible.CheckBox
    Accessible.name: text

    contentItem: Item {
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 4
            Icon { visible: control.checked; name: "check"; size: 12; color: control.fg; anchors.verticalCenter: parent.verticalCenter }
            Text {
                text: control.text
                color: control.fg
                font.family: control.mono ? AppTheme.monoFamily : AppTheme.fontFamily
                font.pixelSize: AppTheme.fontSize.small
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
    background: Rectangle {
        radius: 12
        color: control.checked ? AppTheme.palette.primarySoft : control.hovered ? AppTheme.surfaces.control : "transparent"
        border.width: control.visualFocus ? 2 : 1
        border.color: control.visualFocus ? AppTheme.borders.focus : control.checked ? AppTheme.palette.primaryBorder : AppTheme.borders.strong
    }
}

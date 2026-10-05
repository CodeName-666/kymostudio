// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import Theme 1.0

/** Workbench button: variant "primary" | "neutral" | "ghost" | "danger"; optional stroke icon. */
Button {
    id: control
    property string variant: "neutral"
    property string iconName: ""
    property color toneBackground: "transparent"
    property color toneBorder: "transparent"
    property color toneText: "transparent"
    readonly property bool toned: toneBackground.a > 0
    readonly property color textColor: toned ? toneText
        : variant === "primary" ? AppTheme.palette.primaryText
        : variant === "danger" ? "#F29C99"
        : variant === "ghost" ? (hovered ? AppTheme.text.primary : AppTheme.text.secondary)
        : AppTheme.text.primary

    implicitHeight: AppTheme.heights.control
    padding: 0
    implicitWidth: Math.max(implicitHeight, row.implicitWidth + leftPadding + rightPadding + (text ? 24 : 14))
    font.pixelSize: AppTheme.fontSize.medium
    font.weight: Font.Medium
    opacity: enabled ? 1 : 0.45
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text

    contentItem: Item {
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 6
            Icon { name: control.iconName; visible: control.iconName !== ""; color: control.textColor; anchors.verticalCenter: parent.verticalCenter }
            Text {
                text: control.text
                visible: text !== ""
                font: control.font
                color: control.textColor
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
    background: Rectangle {
        radius: AppTheme.radius.medium
        color: control.toned ? control.toneBackground
            : control.variant === "primary" ? (control.down ? AppTheme.palette.primaryPressed : control.hovered ? AppTheme.palette.primaryHover : AppTheme.palette.primary)
            : control.variant === "danger" ? (control.hovered ? "#3A1717" : "transparent")
            : control.variant === "ghost" ? (control.hovered || control.checked ? AppTheme.surfaces.control : "transparent")
            : (control.down ? AppTheme.buttons.neutral.pressed : control.hovered ? AppTheme.surfaces.controlHover : AppTheme.surfaces.control)
        border.width: control.visualFocus ? 2 : 1
        border.color: control.visualFocus ? AppTheme.borders.focus
            : control.toned ? control.toneBorder
            : control.variant === "primary" ? AppTheme.palette.primary
            : control.variant === "neutral" ? AppTheme.borders.strong : "transparent"
    }
}

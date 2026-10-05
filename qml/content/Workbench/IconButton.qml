import QtQuick 6.4
import QtQuick.Controls 6.4
import Theme 1.0

/** Square icon-only button; `tip` is both tooltip and accessible name. */
ToolButton {
    id: control
    property string iconName: ""
    property string tip: ""
    property color iconColor: hovered ? AppTheme.text.primary : AppTheme.text.secondary
    implicitWidth: 28
    implicitHeight: 28
    padding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: tip
    ToolTip.visible: hovered && tip !== ""
    ToolTip.delay: 500
    ToolTip.text: tip
    opacity: enabled ? 1 : 0.4
    contentItem: Item { Icon { anchors.centerIn: parent; name: control.iconName; color: control.iconColor } }
    background: Rectangle {
        radius: AppTheme.radius.medium
        color: control.down ? AppTheme.buttons.neutral.pressed : control.hovered || control.checked ? AppTheme.surfaces.control : "transparent"
        border.width: control.visualFocus ? 2 : 0
        border.color: AppTheme.borders.focus
    }
}

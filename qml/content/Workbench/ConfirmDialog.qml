import QtQuick 6.4
import QtQuick.Controls 6.4
import Theme 1.0

/**
 * Modal OK/Cancel question. The dialog has a fixed width: sizing it from a
 * wrapped label makes its implicit size depend on itself (binding loop).
 */
Dialog {
    id: root
    property alias text: message.text
    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    width: 440
    standardButtons: Dialog.Ok | Dialog.Cancel
    background: Rectangle { color: AppTheme.surfaces.dialog; border.color: AppTheme.borders.strong; radius: AppTheme.radius.large }
    contentItem: Label {
        id: message
        wrapMode: Text.WordWrap
        color: AppTheme.text.secondary
    }
}

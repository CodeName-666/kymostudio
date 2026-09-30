import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/** Modal dialog frame of the workbench: title bar with close button; set contentItem and footer. */
Dialog {
    id: root
    modal: true
    padding: 0
    closePolicy: Popup.CloseOnEscape

    background: Rectangle { color: AppTheme.surfaces.dialog; border.color: AppTheme.borders.strong; radius: AppTheme.radius.extraLarge }

    header: Item {
        implicitHeight: 52
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 10
            Label { text: root.title; font.pixelSize: AppTheme.fontSize.large; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
            IconButton { iconName: "close"; tip: qsTr("Schließen"); onClicked: root.reject() }
        }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: AppTheme.borders.primary }
    }
}

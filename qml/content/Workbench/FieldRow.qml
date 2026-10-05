import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/**
 * Compact form row: label column on the left, controls in their natural width
 * on the right, optional hint below the controls. Children form the control row.
 */
RowLayout {
    id: root
    property string label
    property string hint
    property bool required: false
    property int labelWidth: 112
    default property alias content: slot.data

    Layout.fillWidth: true
    spacing: 12

    Label {
        text: root.label
        color: AppTheme.text.secondary
        font.pixelSize: AppTheme.fontSize.medium
        elide: Text.ElideRight
        Layout.preferredWidth: root.labelWidth
        Layout.alignment: Qt.AlignTop
        Layout.topMargin: 6
        Label {
            visible: root.required
            x: parent.contentWidth + 3
            text: "*"
            color: AppTheme.palette.primary
            font: parent.font
        }
    }
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4
        RowLayout { id: slot; spacing: 8 }
        Label {
            visible: root.hint !== ""
            text: root.hint
            wrapMode: Text.WordWrap
            color: AppTheme.text.hint
            font.pixelSize: AppTheme.fontSize.small
            Layout.fillWidth: true
        }
    }
}

import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/** Compact colour choice: palette swatches plus a hex field for any other colour. */
RowLayout {
    id: root
    property color color: AppTheme.seriesColors[0]
    readonly property var swatches: AppTheme.seriesColors.concat(["#5FD1C4", "#FF7A73", "#8FA3BF", "#E7ECF3"])
    spacing: 6

    Repeater {
        model: root.swatches
        delegate: AbstractButton {
            id: swatch
            required property string modelData
            readonly property bool selected: Qt.colorEqual(root.color, modelData)
            implicitWidth: 22
            implicitHeight: 22
            hoverEnabled: true
            focusPolicy: Qt.StrongFocus
            Accessible.name: qsTr("Farbe %1").arg(modelData)
            ToolTip.visible: hovered
            ToolTip.delay: 500
            ToolTip.text: modelData
            onClicked: root.color = modelData
            background: Rectangle {
                radius: 6
                color: "transparent"
                border.width: swatch.selected || swatch.visualFocus ? 2 : 0
                border.color: swatch.visualFocus ? AppTheme.borders.focus : AppTheme.text.primary
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: swatch.selected ? 3 : swatch.hovered ? 1 : 2
                    radius: 4
                    color: swatch.modelData
                }
            }
        }
    }
    TextField {
        Layout.preferredWidth: 84
        Layout.leftMargin: 4
        text: root.color.toString().toUpperCase()
        font.family: AppTheme.monoFamily
        font.pixelSize: AppTheme.fontSize.small
        maximumLength: 7
        selectByMouse: true
        validator: RegularExpressionValidator { regularExpression: /#?[0-9A-Fa-f]{0,6}/ }
        Accessible.name: qsTr("Farbe als Hex-Wert")
        onEditingFinished: {
            var value = text.charAt(0) === "#" ? text : "#" + text
            if (/^#[0-9A-Fa-f]{6}$/.test(value)) root.color = value
            else text = root.color.toString().toUpperCase()
        }
    }
}

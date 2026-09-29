import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15

Item {
    id: root

    property color selectedColor: "#ff4444"
    property var predefinedColors: [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
        "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2",
        "#52C41A", "#FA8C16", "#F759AB", "#13C2C2"
    ]

    signal colorSelected(color selectedColor)

    implicitWidth: 320
    implicitHeight: 200

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        // Selected color preview
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: root.selectedColor
            radius: 6
            border.color: "#404040"
            border.width: 2

            Label {
                anchors.centerIn: parent
                text: root.selectedColor.toString().toUpperCase()
                color: getContrastColor(root.selectedColor)
                font.pixelSize: 14
                font.bold: true
            }
        }

        // Predefined colors grid
        Label {
            text: qsTr("Predefined Colors:")
            font.pixelSize: 12
            color: "#cccccc"
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 6
            rowSpacing: 8
            columnSpacing: 8

            Repeater {
                model: root.predefinedColors

                delegate: Rectangle {
                    width: 40
                    height: 40
                    radius: 20
                    color: modelData
                    border.color: root.selectedColor === modelData ? "#ffffff" : "#606060"
                    border.width: root.selectedColor === modelData ? 3 : 1

                    scale: colorMouseArea.pressed ? 0.9 : (colorMouseArea.containsMouse ? 1.1 : 1.0)

                    Behavior on scale {
                        NumberAnimation { duration: 100 }
                    }

                    Behavior on border.width {
                        NumberAnimation { duration: 150 }
                    }

                    MouseArea {
                        id: colorMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            root.selectedColor = modelData
                            root.colorSelected(modelData)
                        }
                    }

                    // Checkmark for selected color
                    Text {
                        anchors.centerIn: parent
                        text: "\u2713"
                        font.pixelSize: 24
                        font.bold: true
                        color: getContrastColor(modelData)
                        visible: root.selectedColor === modelData
                    }
                }
            }
        }

        // Custom color input
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: qsTr("Custom:")
                font.pixelSize: 12
                color: "#cccccc"
            }

            TextField {
                id: customColorInput
                Layout.fillWidth: true
                placeholderText: "#RRGGBB"
                text: root.selectedColor.toString()
                font.pixelSize: 12

                background: Rectangle {
                    color: "#3d3d3d"
                    border.color: customColorInput.activeFocus ? "#007AFF" : "#606060"
                    border.width: 1
                    radius: 4
                }

                color: "#ffffff"

                validator: RegularExpressionValidator {
                    regularExpression: /^#[0-9A-Fa-f]{6}$/
                }

                onAccepted: {
                    if (acceptableInput) {
                        root.selectedColor = text
                        root.colorSelected(text)
                    }
                }
            }

            Button {
                text: qsTr("Apply")
                enabled: customColorInput.acceptableInput

                background: Rectangle {
                    color: parent.enabled ? (parent.hovered ? "#0066CC" : "#007AFF") : "#4d4d4d"
                    radius: 4
                }

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 12
                    color: parent.enabled ? "#ffffff" : "#888888"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    if (customColorInput.acceptableInput) {
                        root.selectedColor = customColorInput.text
                        root.colorSelected(customColorInput.text)
                    }
                }
            }
        }
    }

    // Helper function to get contrasting text color
    function getContrastColor(bgColor) {
        var color = Qt.color(bgColor)
        var luminance = 0.299 * color.r + 0.587 * color.g + 0.114 * color.b
        return luminance > 0.5 ? "#000000" : "#ffffff"
    }
}

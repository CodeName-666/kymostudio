import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15
import Common 1.0
import Backend 1.0
import "../ColorPicker"

Dialog {
    id: root

    title: qsTr("Edit Chart Line")
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel

    // Signals
    signal chartLineUpdated(string lineKey, string displayName, color lineColor)
    signal chartLineDeleted(string lineKey)

    // Properties
    property string lineKey: ""
    property string uniqueId: ""
    property string originalDisplayName: ""
    property color originalColor: "#ff4444"
    property string interfaceType: ""
    property int dataId: 0
    property string chartTitle: ""

    width: 500
    height: 550

    background: Rectangle {
        color: "#2d2d2d"
        border.color: "#4d4d4d"
        border.width: 1
        radius: 8
    }

    header: Rectangle {
        height: 60
        color: "#353535"
        radius: 8

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 4

            Label {
                text: root.title
                font.pixelSize: 18
                font.bold: true
                color: "#ffffff"
            }

            Label {
                text: qsTr("Signal: %1 | Chart: %2 | Interface: %3").arg(root.uniqueId).arg(root.chartTitle || "").arg(root.interfaceType)
                font.pixelSize: 11
                color: "#888888"
            }
        }
    }

    contentItem: Item {
        implicitWidth: 480
        implicitHeight: 490

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 16

            // Info Box
            Rectangle {
                Layout.fillWidth: true
                height: 70
                color: "#353535"
                radius: 6
                border.color: "#4d4d4d"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12

                    // Color preview
                    Rectangle {
                        width: 46
                        height: 46
                        radius: 23
                        color: colorPicker.selectedColor
                        border.color: "#ffffff"
                        border.width: 2
                        Layout.alignment: Qt.AlignVCenter
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Label {
                            text: displayNameInput.text || root.originalDisplayName
                            font.pixelSize: 14
                            font.bold: true
                            color: "#ffffff"
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        Label {
                            text: qsTr("Data ID: %1 | Interface: %2").arg(root.dataId).arg(root.interfaceType)
                            font.pixelSize: 11
                            color: "#aaaaaa"
                        }

                        Label {
                            text: colorPicker.selectedColor.toString().toUpperCase()
                            font.pixelSize: 10
                            color: "#888888"
                        }
                    }
                }
            }

            // Display Name Input
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: qsTr("Display Name") + " *"
                    font.pixelSize: 13
                    font.bold: true
                    color: "#ffffff"
                }

                TextField {
                    id: displayNameInput
                    Layout.fillWidth: true
                    placeholderText: qsTr("e.g., Temperature Sensor")
                    text: root.originalDisplayName

                    background: Rectangle {
                        color: "#3d3d3d"
                        border.color: displayNameInput.activeFocus ? "#007AFF" : "#606060"
                        border.width: 1
                        radius: 4
                    }

                    color: "#ffffff"
                    font.pixelSize: 13

                    validator: RegularExpressionValidator {
                        regularExpression: /.{1,50}/
                    }
                }
            }

            // Color Picker
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: qsTr("Line Color") + " *"
                    font.pixelSize: 13
                    font.bold: true
                    color: "#ffffff"
                }

                ColorPicker {
                    id: colorPicker
                    Layout.fillWidth: true
                    selectedColor: root.originalColor

                    onColorSelected: function(color) {
                        Logger.log_debug("EditChartLineDialog: Color selected: " + color)
                    }
                }
            }

            // Spacer
            Item {
                Layout.fillHeight: true
            }

            // Info text
            Label {
                text: qsTr("* Required fields")
                font.pixelSize: 11
                color: "#888888"
                font.italic: true
            }
        }
    }

    // Custom footer with styled buttons
    footer: Rectangle {
        height: 60
        color: "#353535"
        radius: 8

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Button {
                text: qsTr("Delete")
                Layout.preferredWidth: 100

                background: Rectangle {
                    color: parent.hovered ? "#CC0000" : "#AA0000"
                    radius: 4
                }

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 13
                    font.bold: true
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    deleteConfirmDialog.open()
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: qsTr("Cancel")
                Layout.preferredWidth: 100

                background: Rectangle {
                    color: parent.hovered ? "#4d4d4d" : "#3d3d3d"
                    border.color: "#606060"
                    border.width: 1
                    radius: 4
                }

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 13
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: root.reject()
            }

            Button {
                text: qsTr("Save Changes")
                Layout.preferredWidth: 120
                enabled: isFormValid()

                background: Rectangle {
                    color: parent.enabled ? (parent.hovered ? "#0066CC" : "#007AFF") : "#4d4d4d"
                    radius: 4
                }

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 13
                    font.bold: true
                    color: parent.enabled ? "#ffffff" : "#888888"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: root.accept()
            }
        }
    }

    // Delete Confirmation Dialog
    Dialog {
        id: deleteConfirmDialog
        title: qsTr("Confirm Delete")
        modal: true
        parent: Overlay.overlay
        anchors.centerIn: parent
        implicitWidth: 420

        background: Rectangle {
            color: "#2d2d2d"
            border.color: "#4d4d4d"
            border.width: 1
            radius: 8
        }

        contentItem: ColumnLayout {
            spacing: 16

            Label {
                text: qsTr("Are you sure you want to delete this chart line?")
                font.pixelSize: 13
                color: "#ffffff"
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }

            Label {
                text: root.originalDisplayName + " (" + root.uniqueId + ")"
                font.pixelSize: 12
                font.bold: true
                color: "#FF6B6B"
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }

            Label {
                text: qsTr("This action cannot be undone.")
                font.pixelSize: 11
                color: "#888888"
                font.italic: true
                Layout.fillWidth: true
            }
        }

        footer: Rectangle {
            height: 50
            color: "#353535"
            radius: 8

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12

                Item { Layout.fillWidth: true }

                Button {
                    text: qsTr("Cancel")

                    background: Rectangle {
                        color: parent.hovered ? "#4d4d4d" : "#3d3d3d"
                        border.color: "#606060"
                        border.width: 1
                        radius: 4
                    }

                    contentItem: Text {
                        text: parent.text
                        font.pixelSize: 12
                        color: "#ffffff"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: deleteConfirmDialog.close()
                }

                Button {
                    text: qsTr("Delete")

                    background: Rectangle {
                        color: parent.hovered ? "#CC0000" : "#AA0000"
                        radius: 4
                    }

                    contentItem: Text {
                        text: parent.text
                        font.pixelSize: 12
                        font.bold: true
                        color: "#ffffff"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        deleteConfirmDialog.close()
                        root.chartLineDeleted(root.lineKey)
                        root.close()
                    }
                }
            }
        }
    }

    // Accept handler
    onAccepted: {
        var displayName = displayNameInput.text
        var lineColor = colorPicker.selectedColor

        Logger.log_info("EditChartLineDialog: Saving changes for " + root.uniqueId)
        root.chartLineUpdated(root.lineKey, displayName, lineColor)
    }

    // Helper functions
    function isFormValid() {
        return displayNameInput.text.length > 0
    }

    // Load data when dialog opens
    function loadChartLine(lineKey, uniqueId, displayName, color, interfaceType, dataId, chartTitle) {
        root.lineKey = lineKey
        root.uniqueId = uniqueId
        root.originalDisplayName = displayName
        root.originalColor = color
        root.interfaceType = interfaceType
        root.dataId = dataId
        root.chartTitle = chartTitle || ""

        displayNameInput.text = displayName
        colorPicker.selectedColor = color
    }
}

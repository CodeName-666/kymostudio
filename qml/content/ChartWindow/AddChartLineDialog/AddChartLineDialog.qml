import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15
import Common 1.0
import Backend 1.0
import "../ColorPicker"

Dialog {
    id: root

    title: qsTr("Add Chart Line")
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel

    // Signals
    signal chartLineAdded(string uniqueId, string displayName, color lineColor, string connectionId, int dataId, var interfaceSettings)

    // Properties
    property var availableConnections: []  // Array of connection objects {id, name, type, status}
    property var usedDataIds: []  // Array of used data IDs per connection

    width: 500
    height: 600

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

        Label {
            anchors.centerIn: parent
            text: root.title
            font.pixelSize: 18
            font.bold: true
            color: "#ffffff"
        }
    }

    contentItem: Item {
        implicitWidth: 480
        implicitHeight: 540

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 16

            // Connection Selection
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: qsTr("Connection") + " *"
                    font.pixelSize: 13
                    font.bold: true
                    color: "#ffffff"
                }

                ComboBox {
                    id: connectionCombo
                    Layout.fillWidth: true
                    model: root.availableConnections
                    textRole: "name"
                    enabled: root.availableConnections.length > 0

                    background: Rectangle {
                        color: "#3d3d3d"
                        border.color: connectionCombo.activeFocus ? "#007AFF" : "#606060"
                        border.width: 1
                        radius: 4
                    }

                    contentItem: Text {
                        text: connectionCombo.displayText
                        font: connectionCombo.font
                        color: connectionCombo.enabled ? "#ffffff" : "#888888"
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                    }

                    delegate: ItemDelegate {
                        width: connectionCombo.width

                        contentItem: RowLayout {
                            spacing: 8

                            // Status indicator
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: {
                                    if (!modelData) return "#888888"
                                    switch(modelData.status) {
                                        case "connected": return "#4caf50"
                                        case "connecting": return "#ff9800"
                                        case "disconnected":
                                        default: return "#888888"
                                    }
                                }
                            }

                            // Connection name
                            Text {
                                text: modelData ? modelData.name : ""
                                color: "#ffffff"
                                font: connectionCombo.font
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            // Connection type badge
                            Text {
                                text: modelData ? modelData.type : ""
                                color: "#888888"
                                font.pixelSize: 10
                            }
                        }

                        background: Rectangle {
                            color: parent.hovered ? "#4d4d4d" : "#3d3d3d"
                        }
                    }

                    onCurrentIndexChanged: {
                        updateDataIdSuggestion()
                    }
                }

                // Warning if no connections available
                Label {
                    text: qsTr("⚠ No connections available. Please create a connection first in the side menu.")
                    font.pixelSize: 11
                    color: "#FF6B6B"
                    visible: root.availableConnections.length === 0
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }

            // Data ID Input
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true

                    Label {
                        text: qsTr("Data ID (0-255)") + " *"
                        font.pixelSize: 13
                        font.bold: true
                        color: "#ffffff"
                    }

                    Item { Layout.fillWidth: true }

                    Label {
                        id: dataIdHint
                        text: qsTr("Suggested: ") + getNextAvailableDataId()
                        font.pixelSize: 11
                        color: "#888888"
                    }
                }

                SpinBox {
                    id: dataIdSpinBox
                    Layout.fillWidth: true
                    from: 0
                    to: 255
                    value: getNextAvailableDataId()
                    editable: true

                    background: Rectangle {
                        color: "#3d3d3d"
                        border.color: dataIdSpinBox.activeFocus ? "#007AFF" : (isDataIdUsed(dataIdSpinBox.value) ? "#FF6B6B" : "#606060")
                        border.width: 1
                        radius: 4
                    }

                    contentItem: TextInput {
                        text: dataIdSpinBox.textFromValue(dataIdSpinBox.value, dataIdSpinBox.locale)
                        font: dataIdSpinBox.font
                        color: "#ffffff"
                        horizontalAlignment: Qt.AlignHCenter
                        verticalAlignment: Qt.AlignVCenter
                        readOnly: !dataIdSpinBox.editable
                        validator: dataIdSpinBox.validator
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                    }
                }

                Label {
                    text: qsTr("⚠ Warning: Data ID %1 is already in use for this connection").arg(dataIdSpinBox.value)
                    font.pixelSize: 11
                    color: "#FF6B6B"
                    visible: isDataIdUsed(dataIdSpinBox.value)
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
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
                    text: getDefaultDisplayName()

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
                    selectedColor: getDefaultColor()

                    onColorSelected: function(color) {
                        Logger.log_debug("AddChartLineDialog: Color selected: " + color)
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
                text: qsTr("Add Line")
                Layout.preferredWidth: 100
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

    // Accept handler
    onAccepted: {
        // Get selected connection
        var selectedConnection = getSelectedConnection()
        if (!selectedConnection) {
            Logger.log_error("AddChartLineDialog: No connection selected")
            return
        }

        var connectionId = selectedConnection.id
        var dataId = dataIdSpinBox.value
        var uniqueId = connectionId + "_" + dataId
        var displayName = displayNameInput.text
        var lineColor = colorPicker.selectedColor

        Logger.log_info("AddChartLineDialog: Adding chart line - " + uniqueId)

        root.chartLineAdded(uniqueId, displayName, lineColor, connectionId, dataId, {})
    }

    // Helper functions
    function getSelectedConnection() {
        if (connectionCombo.currentIndex >= 0 && connectionCombo.currentIndex < root.availableConnections.length) {
            return root.availableConnections[connectionCombo.currentIndex]
        }
        return null
    }

    function isFormValid() {
        return displayNameInput.text.length > 0 &&
               dataIdSpinBox.value >= 0 &&
               dataIdSpinBox.value <= 255 &&
               root.availableConnections.length > 0 &&
               connectionCombo.currentIndex >= 0
    }

    function isDataIdUsed(dataId) {
        var selectedConnection = getSelectedConnection()
        if (!selectedConnection) {
            return false
        }

        var connectionId = selectedConnection.id
        var uniqueId = connectionId + "_" + dataId

        // Check in usedDataIds array
        for (var i = 0; i < usedDataIds.length; i++) {
            if (usedDataIds[i] === uniqueId) {
                return true
            }
        }
        return false
    }

    function getNextAvailableDataId() {
        var selectedConnection = getSelectedConnection()
        if (!selectedConnection) {
            return 0
        }

        var connectionId = selectedConnection.id

        for (var i = 0; i <= 255; i++) {
            var uniqueId = connectionId + "_" + i
            var found = false

            for (var j = 0; j < usedDataIds.length; j++) {
                if (usedDataIds[j] === uniqueId) {
                    found = true
                    break
                }
            }

            if (!found) {
                return i
            }
        }

        return 0
    }

    function updateDataIdSuggestion() {
        dataIdSpinBox.value = getNextAvailableDataId()
        displayNameInput.text = getDefaultDisplayName()
    }

    function getDefaultDisplayName() {
        var selectedConnection = getSelectedConnection()
        if (!selectedConnection) {
            return "Chart Line"
        }

        var dataId = dataIdSpinBox.value
        return selectedConnection.name + " #" + dataId
    }

    function getDefaultColor() {
        var colors = colorPicker.predefinedColors
        var dataId = dataIdSpinBox.value
        return colors[dataId % colors.length]
    }

    function refreshConnectionsList(connections, usedIds) {
        root.availableConnections = connections
        root.usedDataIds = usedIds
        updateDataIdSuggestion()
    }

    // Reset when opening
    Component.onCompleted: {
        updateDataIdSuggestion()
    }

    onAboutToShow: {
        // Refresh when dialog opens
        updateDataIdSuggestion()
    }
}

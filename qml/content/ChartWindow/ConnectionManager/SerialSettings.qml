import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15
import Common 1.0
import Theme 1.0
import Backend 1.0

ColumnLayout {
    id: root

    spacing: 12

    // COM Port
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Port") + " *"
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        ComboBox {
            id: portCombo
            Layout.fillWidth: true
            editable: true
            font.pixelSize: 12
            textRole: "text"

            model: ListModel {
                id: portsModel
            }

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: TextInput {
                text: portCombo.displayText
                font: portCombo.font
                color: AppTheme.text.primary
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
                readOnly: !portCombo.editable
                selectByMouse: true
            }
        }

        Button {
            text: qsTr("Ports neu einlesen")
            Layout.fillWidth: true
            font.pixelSize: 11

            background: Rectangle {
                color: parent.pressed ? AppTheme.borders.primary : (parent.hovered ? "#5d5d5d" : AppTheme.inputs.background)
                border.color: AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: Text {
                text: parent.text
                color: AppTheme.text.primary
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font: parent.font
            }

            onClicked: {
                refreshPorts()
            }
        }
    }

    // Baud Rate
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Baudrate") + " *"
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        ComboBox {
            id: baudCombo
            Layout.fillWidth: true
            font.pixelSize: 12

            model: ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
            currentIndex: 7  // Default to 115200

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: Text {
                text: baudCombo.displayText
                font: baudCombo.font
                color: AppTheme.text.primary
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
            }
        }
    }

    // Data Bits
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Datenbits")
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        ComboBox {
            id: dataBitsCombo
            Layout.fillWidth: true
            font.pixelSize: 12

            model: ["5", "6", "7", "8"]
            currentIndex: 3  // Default to 8

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: Text {
                text: dataBitsCombo.displayText
                font: dataBitsCombo.font
                color: AppTheme.text.primary
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
            }
        }
    }

    // Parity
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Parität")
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        ComboBox {
            id: parityCombo
            Layout.fillWidth: true
            font.pixelSize: 12

            model: ["None", "Even", "Odd", "Mark", "Space"]
            currentIndex: 0  // Default to None

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: Text {
                text: parityCombo.displayText
                font: parityCombo.font
                color: AppTheme.text.primary
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
            }
        }
    }

    // Stop Bits
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Stoppbits")
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        ComboBox {
            id: stopBitsCombo
            Layout.fillWidth: true
            font.pixelSize: 12

            model: ["1", "1.5", "2"]
            currentIndex: 0  // Default to 1

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: Text {
                text: stopBitsCombo.displayText
                font: stopBitsCombo.font
                color: AppTheme.text.primary
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
            }
        }
    }

    Item {
        Layout.fillHeight: true
    }

    Component.onCompleted: {
        refreshPorts()
    }

    // Backend connection for COM port updates
    Connections {
        target: Backend
        function onCom_port_update(portList) {
            updatePortsList(portList)
        }
    }

    // Functions
    function refreshPorts() {
        Logger.log_debug("Refreshing COM ports...")
        if(typeof Backend !== "undefined" && typeof Backend.get_com_ports === "function") {
            var ports = Backend.get_com_ports()
            if(ports !== undefined && ports !== null) {
                updatePortsList(ports)
            }
        } else {
            Logger.log_warning("SerialSettings: Backend.get_com_ports not available")
        }
    }

    function updatePortsList(ports) {
        var currentPort = portCombo.editText
        portsModel.clear()

        for(var i = 0; i < ports.length; i++) {
            portsModel.append({"text": ports[i]})
        }

        // Restore selection if port still exists
        if(currentPort) {
            for(var j = 0; j < portsModel.count; j++) {
                if(portsModel.get(j).text === currentPort) {
                    portCombo.currentIndex = j
                    return
                }
            }
            portCombo.editText = currentPort
        } else if(portsModel.count > 0) {
            portCombo.currentIndex = 0
        }
    }

    function loadDefaults(defaults) {
        if(defaults.port) {
            portCombo.editText = defaults.port
        }
        if(defaults.baud) {
            var baudIndex = baudCombo.model.indexOf(defaults.baud.toString())
            if(baudIndex >= 0) {
                baudCombo.currentIndex = baudIndex
            }
        }
        if(defaults.size) {
            var sizeIndex = dataBitsCombo.model.indexOf(defaults.size.toString())
            if(sizeIndex >= 0) {
                dataBitsCombo.currentIndex = sizeIndex
            }
        }
        if(defaults.parity) {
            var parityIndex = parityCombo.model.indexOf(defaults.parity)
            if(parityIndex >= 0) {
                parityCombo.currentIndex = parityIndex
            }
        }
        if(defaults.stop_bits) {
            var stopIndex = stopBitsCombo.model.indexOf(defaults.stop_bits.toString())
            if(stopIndex >= 0) {
                stopBitsCombo.currentIndex = stopIndex
            }
        }
    }

    function getSettings() {
        return {
            "port": portCombo.editText,
            "baud": parseInt(baudCombo.currentText),
            "size": parseInt(dataBitsCombo.currentText),
            "parity": parityCombo.currentText,
            "stop_bits": parseFloat(stopBitsCombo.currentText)
        }
    }
}

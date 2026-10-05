// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Common 1.0
import Theme 1.0
import Backend 1.0
import "../../Workbench"

/** Serial (UART) source settings. Keys: port, baud, size, parity, stop_bits. */
ColumnLayout {
    id: root
    spacing: 20

    readonly property var dataBits: ["5", "6", "7", "8"]
    readonly property var parities: ["None", "Even", "Odd", "Mark", "Space"]
    readonly property var stopBits: ["1", "1.5", "2"]

    FormSection {
        title: qsTr("Anschluss")
        FieldRow {
            label: qsTr("Port")
            required: true
            ComboBox {
                id: portCombo
                Layout.preferredWidth: 180
                editable: true
                textRole: "text"
                model: ListModel { id: portsModel }
                Accessible.name: qsTr("COM-Port")
            }
            IconButton { iconName: "refresh"; tip: qsTr("Ports neu einlesen"); onClicked: root.refreshPorts() }
        }
        FieldRow {
            label: qsTr("Baudrate")
            required: true
            ComboBox {
                id: baudCombo
                Layout.preferredWidth: 120
                model: ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
                currentIndex: 7
                Accessible.name: qsTr("Baudrate")
            }
            Label { text: qsTr("Bit/s"); color: AppTheme.text.hint }
        }
    }

    FormSection {
        title: qsTr("Rahmenformat")
        FieldRow {
            label: qsTr("Datenbits")
            Segmented { id: dataBitsSeg; accessibleName: qsTr("Datenbits"); options: root.dataBits.map(function(v) { return { text: v } }); currentIndex: 3 }
        }
        FieldRow {
            label: qsTr("Parität")
            Segmented {
                id: paritySeg
                accessibleName: qsTr("Parität")
                options: [{ text: qsTr("Keine") }, { text: qsTr("Gerade") }, { text: qsTr("Ungerade") }, { text: "Mark" }, { text: "Space" }]
                currentIndex: 0
            }
        }
        FieldRow {
            label: qsTr("Stoppbits")
            hint: qsTr("Üblich ist 8N1: 8 Datenbits, keine Parität, 1 Stoppbit.")
            Segmented { id: stopBitsSeg; accessibleName: qsTr("Stoppbits"); options: [{ text: "1" }, { text: "1,5" }, { text: "2" }]; currentIndex: 0 }
        }
    }

    Component.onCompleted: refreshPorts()

    Connections {
        target: Backend
        function onCom_port_update(portList) { root.updatePortsList(portList) }
    }

    function refreshPorts() {
        if (typeof Backend !== "undefined" && typeof Backend.get_com_ports === "function") {
            var ports = Backend.get_com_ports()
            if (ports !== undefined && ports !== null) updatePortsList(ports)
        } else {
            Logger.log_warning("SerialSettings: Backend.get_com_ports not available")
        }
    }

    function updatePortsList(ports) {
        var currentPort = portCombo.editText
        portsModel.clear()
        for (var i = 0; i < ports.length; i++) portsModel.append({ "text": ports[i] })
        if (currentPort) {
            for (var j = 0; j < portsModel.count; j++) {
                if (portsModel.get(j).text === currentPort) { portCombo.currentIndex = j; return }
            }
            portCombo.editText = currentPort
        } else if (portsModel.count > 0) {
            portCombo.currentIndex = 0
        }
    }

    function loadDefaults(defaults) {
        if (defaults.port) portCombo.editText = defaults.port
        if (defaults.baud) {
            var baudIndex = baudCombo.model.indexOf(defaults.baud.toString())
            if (baudIndex >= 0) baudCombo.currentIndex = baudIndex
        }
        // Config templates may carry "8Bit"/"1Bit"; only the number matters.
        var size = String(parseInt(defaults.size)), stop = String(parseFloat(defaults.stop_bits))
        if (dataBits.indexOf(size) >= 0) dataBitsSeg.currentIndex = dataBits.indexOf(size)
        if (defaults.parity && parities.indexOf(defaults.parity) >= 0) paritySeg.currentIndex = parities.indexOf(defaults.parity)
        if (stopBits.indexOf(stop) >= 0) stopBitsSeg.currentIndex = stopBits.indexOf(stop)
    }

    function getSettings() {
        return {
            "port": portCombo.editText,
            "baud": parseInt(baudCombo.currentText),
            // The serial receiver keys byte size and stop bits as "8Bit" / "1Bit".
            "size": dataBits[dataBitsSeg.currentIndex] + "Bit",
            "parity": parities[paritySeg.currentIndex],
            "stop_bits": stopBits[stopBitsSeg.currentIndex] + "Bit"
        }
    }
}

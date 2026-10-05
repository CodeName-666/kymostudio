// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0
import "../../Workbench"

/** CAN source settings. Keys: interface, channel, bitrate, value_format, scale, offset, data_id?, tx_id?. */
ColumnLayout {
    id: root
    spacing: 20

    FormSection {
        title: qsTr("Adapter")
        FieldRow {
            label: qsTr("Treiber")
            required: true
            ComboBox {
                id: interfaceCombo
                Layout.preferredWidth: 150
                editable: true
                model: ["virtual", "socketcan", "pcan", "vector", "kvaser", "ixxat", "slcan"]
                Accessible.name: qsTr("CAN-Treiber")
            }
        }
        FieldRow {
            label: qsTr("Kanal")
            required: true
            TextField { id: channelField; Layout.preferredWidth: 200; text: "kymo"; placeholderText: qsTr("can0, PCAN_USBBUS1 …"); selectByMouse: true; Accessible.name: qsTr("Kanal") }
        }
        FieldRow {
            label: qsTr("Bitrate")
            TextField { id: bitrateField; Layout.preferredWidth: 100; text: "500000"; selectByMouse: true; Accessible.name: qsTr("Bitrate"); validator: IntValidator { bottom: 1 } }
            Label { text: qsTr("Bit/s"); color: AppTheme.text.hint }
        }
    }

    FormSection {
        title: qsTr("Dekodierung")
        FieldRow {
            label: qsTr("Nutzdaten")
            hint: qsTr("„auto“: 4 Byte als Float32, 8 Byte als Float64, andere Längen als vorzeichenlose Ganzzahl.")
            ComboBox {
                id: valueFormatCombo
                Layout.preferredWidth: 150
                model: ["auto", "float32_le", "float32_be", "float64_le", "float64_be", "uint_le", "uint_be", "int_le", "int_be"]
                Accessible.name: qsTr("Nutzdatenformat")
            }
        }
        FieldRow {
            label: qsTr("Umrechnung")
            hint: qsTr("Angezeigter Wert = Rohwert × Faktor + Offset")
            Label { text: "×"; color: AppTheme.text.hint }
            TextField { id: scaleField; Layout.preferredWidth: 80; text: "1.0"; selectByMouse: true; Accessible.name: qsTr("Faktor"); validator: DoubleValidator {} }
            Label { text: "+"; color: AppTheme.text.hint }
            TextField { id: offsetField; Layout.preferredWidth: 80; text: "0.0"; selectByMouse: true; Accessible.name: qsTr("Offset"); validator: DoubleValidator {} }
        }
        FieldRow {
            label: qsTr("Daten-ID")
            hint: qsTr("Optional; sonst CAN-ID modulo 256.")
            TextField { id: dataIdField; Layout.preferredWidth: 80; placeholderText: qsTr("auto"); selectByMouse: true; Accessible.name: qsTr("Daten-ID"); validator: IntValidator { bottom: 0; top: 255 } }
        }
        FieldRow {
            label: qsTr("Sende-CAN-ID")
            TextField { id: txIdField; Layout.preferredWidth: 100; placeholderText: "0x123"; selectByMouse: true; Accessible.name: qsTr("Sende-CAN-ID") }
            Label { text: qsTr("optional"); color: AppTheme.text.hint }
        }
    }

    function loadDefaults(defaults) {
        var backendName = defaults.interface || defaults.bustype || "virtual"
        var backendIndex = interfaceCombo.find(backendName)
        if (backendIndex >= 0) interfaceCombo.currentIndex = backendIndex
        else interfaceCombo.editText = backendName
        if (defaults.channel !== undefined) channelField.text = defaults.channel.toString()
        if (defaults.bitrate !== undefined) bitrateField.text = defaults.bitrate.toString()
        if (defaults.value_format) {
            var formatIndex = valueFormatCombo.find(defaults.value_format)
            if (formatIndex >= 0) valueFormatCombo.currentIndex = formatIndex
        }
        if (defaults.scale !== undefined) scaleField.text = defaults.scale.toString()
        if (defaults.offset !== undefined) offsetField.text = defaults.offset.toString()
        dataIdField.text = defaults.data_id !== undefined && defaults.data_id !== null ? defaults.data_id.toString() : ""
        txIdField.text = defaults.tx_id !== undefined && defaults.tx_id !== null ? defaults.tx_id.toString() : ""
    }

    function getSettings() {
        var settings = {
            "interface": interfaceCombo.editText.trim(),
            "channel": channelField.text.trim(),
            "bitrate": parseInt(bitrateField.text),
            "value_format": valueFormatCombo.currentText,
            "scale": parseFloat(scaleField.text),
            "offset": parseFloat(offsetField.text)
        }
        if (dataIdField.text.trim() !== "") settings.data_id = parseInt(dataIdField.text)
        if (txIdField.text.trim() !== "") settings.tx_id = txIdField.text.trim()
        return settings
    }
}

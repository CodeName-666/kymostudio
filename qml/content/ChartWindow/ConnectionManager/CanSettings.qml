import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15

ScrollView {
    id: root

    clip: true
    contentWidth: availableWidth

    ColumnLayout {
        width: root.availableWidth
        spacing: 12

        Label {
            text: qsTr("CAN-Treiber") + " *"
            color: AppTheme.text.primary
            font.bold: true
        }

        ComboBox {
            id: interfaceCombo
            Layout.fillWidth: true
            editable: true
            model: ["virtual", "socketcan", "pcan", "vector", "kvaser", "ixxat", "slcan"]
            currentIndex: 0
        }

        Label {
            text: qsTr("Kanal") + " *"
            color: AppTheme.text.primary
            font.bold: true
        }

        TextField {
            id: channelField
            Layout.fillWidth: true
            text: "plotter"
            placeholderText: qsTr("z. B. can0, PCAN_USBBUS1 oder plotter")
            color: AppTheme.text.primary
        }

        Label {
            text: qsTr("Bitrate")
            color: AppTheme.text.primary
            font.bold: true
        }

        TextField {
            id: bitrateField
            Layout.fillWidth: true
            text: "500000"
            validator: IntValidator { bottom: 1 }
            color: AppTheme.text.primary
        }

        Label {
            text: qsTr("Nutzdatenformat")
            color: AppTheme.text.primary
            font.bold: true
        }

        ComboBox {
            id: valueFormatCombo
            Layout.fillWidth: true
            model: [
                "auto", "float32_le", "float32_be", "float64_le", "float64_be",
                "uint_le", "uint_be", "int_le", "int_be"
            ]
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 8
            rowSpacing: 6

            Label { text: qsTr("Skalierung"); color: AppTheme.text.primary }
            TextField {
                id: scaleField
                Layout.fillWidth: true
                text: "1.0"
                validator: DoubleValidator {}
                color: AppTheme.text.primary
            }

            Label { text: qsTr("Offset"); color: AppTheme.text.primary }
            TextField {
                id: offsetField
                Layout.fillWidth: true
                text: "0.0"
                validator: DoubleValidator {}
                color: AppTheme.text.primary
            }

            Label { text: qsTr("Daten-ID (optional)"); color: AppTheme.text.primary }
            TextField {
                id: dataIdField
                Layout.fillWidth: true
                placeholderText: qsTr("Sonst CAN-ID modulo 256")
                validator: IntValidator { bottom: 0; top: 255 }
                color: AppTheme.text.primary
            }

            Label { text: qsTr("Sende-CAN-ID (optional)"); color: AppTheme.text.primary }
            TextField {
                id: txIdField
                Layout.fillWidth: true
                placeholderText: qsTr("z. B. 0x123")
                color: AppTheme.text.primary
            }
        }

        Label {
            Layout.fillWidth: true
            text: qsTr("Auto dekodiert 4-Byte-Nutzdaten als Float32, 8-Byte-Nutzdaten als Float64 und andere Längen als vorzeichenlose Ganzzahlen.")
            color: "#a0a0a0"
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }

        Item { Layout.fillHeight: true }
    }

    function loadDefaults(defaults) {
        var backendName = defaults.interface || defaults.bustype || "virtual"
        var backendIndex = interfaceCombo.find(backendName)
        if (backendIndex >= 0)
            interfaceCombo.currentIndex = backendIndex
        else
            interfaceCombo.editText = backendName

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
            "interface": interfaceCombo.currentText.trim(),
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

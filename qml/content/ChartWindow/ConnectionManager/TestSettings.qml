import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 1.15
import Common 1.0
import Theme 1.0

ColumnLayout {
    id: root

    spacing: 12

    // Signal Type
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Signaltyp") + " *"
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        ComboBox {
            id: typeCombo
            Layout.fillWidth: true
            font.pixelSize: 12

            model: ["sinus", "ramp", "random", "multi"]
            currentIndex: 0

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: Text {
                text: typeCombo.displayText
                font: typeCombo.font
                color: AppTheme.text.primary
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
            }
        }

        Label {
            text: getTypeDescription()
            font.pixelSize: 10
            color: "#808080"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }

    // Frequency
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Frequenz (Hz)")
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        SpinBox {
            id: frequencySpinBox
            Layout.fillWidth: true
            from: 1
            to: 100
            value: 1
            editable: true
            font.pixelSize: 12

            property int decimals: 1
            property real realValue: value / 10.0

            validator: DoubleValidator {
                bottom: Math.min(frequencySpinBox.from, frequencySpinBox.to)
                top: Math.max(frequencySpinBox.from, frequencySpinBox.to)
            }

            textFromValue: function(value, locale) {
                return Number(value / 10.0).toLocaleString(locale, 'f', 1)
            }

            valueFromText: function(text, locale) {
                return Number.fromLocaleString(locale, text) * 10
            }

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: TextInput {
                text: frequencySpinBox.textFromValue(frequencySpinBox.value, frequencySpinBox.locale)
                font: frequencySpinBox.font
                color: AppTheme.text.primary
                horizontalAlignment: Qt.AlignHCenter
                verticalAlignment: Qt.AlignVCenter
                readOnly: !frequencySpinBox.editable
                validator: frequencySpinBox.validator
            }

            up.indicator: Rectangle {
                x: frequencySpinBox.width - width
                height: parent.height / 2
                color: frequencySpinBox.up.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "+"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }

            down.indicator: Rectangle {
                x: frequencySpinBox.width - width
                y: parent.height / 2
                height: parent.height / 2
                color: frequencySpinBox.down.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "-"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }
        }
    }

    // Amplitude
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Amplitude")
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        SpinBox {
            id: amplitudeSpinBox
            Layout.fillWidth: true
            from: 10
            to: 10000
            value: 100
            stepSize: 10
            editable: true
            font.pixelSize: 12

            property int decimals: 1
            property real realValue: value / 10.0

            textFromValue: function(value, locale) {
                return Number(value / 10.0).toLocaleString(locale, 'f', 1)
            }

            valueFromText: function(text, locale) {
                return Number.fromLocaleString(locale, text) * 10
            }

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: TextInput {
                text: amplitudeSpinBox.textFromValue(amplitudeSpinBox.value, amplitudeSpinBox.locale)
                font: amplitudeSpinBox.font
                color: AppTheme.text.primary
                horizontalAlignment: Qt.AlignHCenter
                verticalAlignment: Qt.AlignVCenter
                readOnly: !amplitudeSpinBox.editable
                validator: amplitudeSpinBox.validator
            }

            up.indicator: Rectangle {
                x: amplitudeSpinBox.width - width
                height: parent.height / 2
                color: amplitudeSpinBox.up.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "+"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }

            down.indicator: Rectangle {
                x: amplitudeSpinBox.width - width
                y: parent.height / 2
                height: parent.height / 2
                color: amplitudeSpinBox.down.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "-"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }
        }
    }

    // Sample Rate
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            text: qsTr("Abtastintervall (ms)")
            font.pixelSize: 12
            font.bold: true
            color: AppTheme.text.primary
        }

        SpinBox {
            id: sampleRateSpinBox
            Layout.fillWidth: true
            from: 10
            to: 10000
            value: 100
            stepSize: 10
            editable: true
            font.pixelSize: 12

            background: Rectangle {
                color: AppTheme.inputs.background
                border.color: parent.activeFocus ? AppTheme.palette.primary : AppTheme.borders.primary
                border.width: 1
                radius: 4
            }

            contentItem: TextInput {
                text: sampleRateSpinBox.textFromValue(sampleRateSpinBox.value, sampleRateSpinBox.locale)
                font: sampleRateSpinBox.font
                color: AppTheme.text.primary
                horizontalAlignment: Qt.AlignHCenter
                verticalAlignment: Qt.AlignVCenter
                readOnly: !sampleRateSpinBox.editable
                validator: sampleRateSpinBox.validator
            }

            up.indicator: Rectangle {
                x: sampleRateSpinBox.width - width
                height: parent.height / 2
                color: sampleRateSpinBox.up.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "+"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }

            down.indicator: Rectangle {
                x: sampleRateSpinBox.width - width
                y: parent.height / 2
                height: parent.height / 2
                color: sampleRateSpinBox.down.pressed ? "#5d5d5d" : AppTheme.borders.primary
                border.color: AppTheme.borders.primary

                Text {
                    text: "-"
                    font.pixelSize: 14
                    color: AppTheme.text.primary
                    anchors.centerIn: parent
                }
            }
        }

        Label {
            text: qsTr("Wie oft neue Datenpunkte erzeugt werden")
            font.pixelSize: 10
            color: "#808080"
        }
    }

    Item {
        Layout.fillHeight: true
    }

    // Functions
    function getTypeDescription() {
        switch(typeCombo.currentText) {
            case "sinus":
                return qsTr("Sinussignal")
            case "ramp":
                return qsTr("Lineare Rampe")
            case "random":
                return qsTr("Zufallsrauschen")
            case "multi":
                return qsTr("Mehrere Signale (Sinus + Rauschen)")
            default:
                return ""
        }
    }

    function loadDefaults(defaults) {
        if(defaults.type) {
            var typeIndex = typeCombo.model.indexOf(defaults.type)
            if(typeIndex >= 0) {
                typeCombo.currentIndex = typeIndex
            }
        }
        if(defaults.frequency !== undefined) {
            frequencySpinBox.value = defaults.frequency * 10
        }
        if(defaults.amplitude !== undefined) {
            amplitudeSpinBox.value = defaults.amplitude * 10
        }
        if(defaults.sample_ms !== undefined) {
            sampleRateSpinBox.value = defaults.sample_ms
        }
    }

    function getSettings() {
        return {
            "type": typeCombo.currentText,
            "frequency": frequencySpinBox.realValue,
            "amplitude": amplitudeSpinBox.realValue,
            "sample_ms": sampleRateSpinBox.value
        }
    }
}

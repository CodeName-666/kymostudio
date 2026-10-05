import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0
import "../../Workbench"

/** Synthetic test source. Keys: type, frequency (Hz), amplitude, sample_ms. */
ColumnLayout {
    id: root
    spacing: 20

    readonly property var types: ["sinus", "ramp", "random", "multi"]
    readonly property var descriptions: [
        qsTr("Sinus, Kosinus und doppelter Sinus."),
        qsTr("Lineare Rampe."),
        qsTr("Zufallsrauschen."),
        qsTr("Mehrere Signale aus Sinus und Rauschen.")
    ]

    // One decimal place, stored ×10 in the integer SpinBox.
    component TenthSpinBox: SpinBox {
        editable: true
        Layout.preferredWidth: 120
        readonly property real realValue: value / 10.0
        validator: DoubleValidator { bottom: from / 10.0; top: to / 10.0; decimals: 1 }
        textFromValue: function(v, locale) { return Number(v / 10.0).toLocaleString(locale, "f", 1) }
        valueFromText: function(text, locale) { return Math.round(Number.fromLocaleString(locale, text) * 10) }
    }

    FormSection {
        title: qsTr("Generator")
        FieldRow {
            label: qsTr("Signalform")
            required: true
            hint: root.descriptions[typeSeg.currentIndex]
            Segmented {
                id: typeSeg
                accessibleName: qsTr("Signalform")
                options: [{ text: qsTr("Sinus") }, { text: qsTr("Rampe") }, { text: qsTr("Rauschen") }, { text: qsTr("Mehrfach") }]
                currentIndex: 0
            }
        }
        FieldRow {
            label: qsTr("Frequenz")
            TenthSpinBox { id: frequencySpinBox; from: 1; to: 100; value: 1; Accessible.name: qsTr("Frequenz in Hertz") }
            Label { text: "Hz"; color: AppTheme.text.hint }
        }
        FieldRow {
            label: qsTr("Amplitude")
            TenthSpinBox { id: amplitudeSpinBox; from: 10; to: 10000; stepSize: 10; value: 100; Accessible.name: qsTr("Amplitude") }
        }
        FieldRow {
            label: qsTr("Abtastintervall")
            hint: qsTr("Abstand zwischen zwei erzeugten Datenpunkten.")
            SpinBox { id: sampleRateSpinBox; from: 10; to: 10000; stepSize: 10; value: 100; editable: true; Layout.preferredWidth: 120; Accessible.name: qsTr("Abtastintervall in Millisekunden") }
            Label { text: "ms"; color: AppTheme.text.hint }
        }
    }

    function loadDefaults(defaults) {
        if (defaults.type && types.indexOf(defaults.type) >= 0) typeSeg.currentIndex = types.indexOf(defaults.type)
        if (defaults.frequency !== undefined) frequencySpinBox.value = Math.round(defaults.frequency * 10)
        if (defaults.amplitude !== undefined) amplitudeSpinBox.value = Math.round(defaults.amplitude * 10)
        if (defaults.sample_ms !== undefined) sampleRateSpinBox.value = defaults.sample_ms
    }

    function getSettings() {
        return {
            "type": types[typeSeg.currentIndex],
            "frequency": frequencySpinBox.realValue,
            "amplitude": amplitudeSpinBox.realValue,
            "sample_ms": sampleRateSpinBox.value
        }
    }
}

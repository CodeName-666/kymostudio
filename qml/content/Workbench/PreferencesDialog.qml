import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

Dialog {
    id: root
    title: qsTr("Darstellung & Leistung")
    modal: true
    width: Math.min(610, parent ? parent.width - 32 : 610)
    height: Math.min(620, parent ? parent.height - 40 : 620)
    standardButtons: Dialog.Apply | Dialog.Close
    property var backendInterface
    signal preferencesApplied()
    readonly property var intervals: [16, 33, 50, 100, 200]

    onAboutToShow: {
        var p = backendInterface.get_performance_settings()
        grid.checked = AppTheme.showGrid
        legend.checked = AppTheme.showLegend
        cursor.checked = AppTheme.showCrosshair
        smooth.checked = AppTheme.antialiasing
        pointLimit.value = p.display_points_per_signal
        rate.currentIndex = Math.max(0, intervals.indexOf(p.frame_interval_ms))
        reduction.checked = p.downsample_enabled
        targetRate.value = p.downsample_target_hz
    }
    onApplied: {
        var settings = { frame_interval_ms: intervals[rate.currentIndex],
            display_points_per_signal: pointLimit.value, downsample_enabled: reduction.checked,
            downsample_target_hz: targetRate.value }
        if (backendInterface.apply_performance_settings(settings)) {
            AppTheme.showGrid = grid.checked
            AppTheme.showLegend = legend.checked
            AppTheme.showCrosshair = cursor.checked
            AppTheme.antialiasing = smooth.checked
            AppTheme.displayPointLimit = pointLimit.value
            preferencesApplied()
        }
    }
    contentItem: ScrollView {
            id: preferencesScroll
        clip: true
        ColumnLayout {
            width: preferencesScroll.availableWidth
            spacing: 10
            Label { text: qsTr("Diagramme"); font.bold: true; font.pixelSize: 16 }
            CheckBox { id: grid; text: qsTr("Gitternetz anzeigen") }
            CheckBox { id: legend; text: qsTr("Legende anzeigen") }
            CheckBox { id: cursor; text: qsTr("Koordinaten-Fadenkreuz in 2D anzeigen") }
            CheckBox { id: smooth; text: qsTr("Kantenglättung · kann mehr Grafikleistung benötigen") }
            MenuSeparator { Layout.fillWidth: true }
            Label { text: qsTr("Live-Anzeige"); font.bold: true; font.pixelSize: 16 }
            GridLayout {
                columns: 2
                Layout.fillWidth: true
                columnSpacing: 16
                Label { text: qsTr("Aktualisierungsintervall") }
                ComboBox { id: rate; Layout.fillWidth: true; model: ["16 ms · bis zu 60 Hz", "33 ms · bis zu 30 Hz", "50 ms · bis zu 20 Hz", "100 ms · bis zu 10 Hz", "200 ms · bis zu 5 Hz"] }
                Label { text: qsTr("Punkte pro 2D-Kurve") }
                SpinBox { id: pointLimit; from: 500; to: 50000; stepSize: 500; editable: true; Layout.fillWidth: true }
            }
            CheckBox { id: reduction; text: qsTr("Y-Daten ohne explizites X für die Anzeige verdichten") }
            RowLayout {
                enabled: reduction.checked
                Label { text: qsTr("Zielwerte pro Sekunde"); Layout.fillWidth: true }
                SpinBox { id: targetRate; from: 10; to: 5000; stepSize: 10; editable: true }
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: AppTheme.text.secondary
                text: qsTr("Die Verdichtung erhält lokale Minima und Maxima innerhalb eines Pakets. Statistik und CSV verwenden den separaten Rohdatenpuffer, nicht die verdichtete Kurve. Die tatsächliche Bildrate hängt von Datenmenge und Hardware ab.")
            }
            MenuSeparator { Layout.fillWidth: true }
            Label {
                Layout.fillWidth: true; wrapMode: Text.WordWrap; color: AppTheme.text.secondary
                text: qsTr("Speichergrenzen: bis zu 20.000 Rohwerte pro Signal, insgesamt 250.000 Werte. Bei Überlast werden alte Werte verworfen. Die Statusleiste zeigt Verluste an; diese App ist kein verlustfreier Langzeitrekorder.")
            }
        }
    }
}

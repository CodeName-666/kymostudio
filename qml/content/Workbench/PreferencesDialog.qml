import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

WorkbenchDialog {
    id: root
    title: qsTr("Darstellung & Leistung")
    width: Math.min(560, parent ? parent.width - 32 : 560)
    height: Math.min(660, parent ? parent.height - 40 : 660)
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
    function apply() {
        var settings = { frame_interval_ms: intervals[rate.currentIndex],
            display_points_per_signal: pointLimit.value, downsample_enabled: reduction.checked,
            downsample_target_hz: targetRate.value }
        if (!backendInterface.apply_performance_settings(settings)) return false
        AppTheme.showGrid = grid.checked
        AppTheme.showLegend = legend.checked
        AppTheme.showCrosshair = cursor.checked
        AppTheme.antialiasing = smooth.checked
        AppTheme.displayPointLimit = pointLimit.value
        preferencesApplied()
        return true
    }

    contentItem: ScrollView {
        id: preferencesScroll
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            x: 20
            width: preferencesScroll.availableWidth - 40
            spacing: 20
            Item { implicitHeight: 2 }

            FormSection {
                title: qsTr("Diagramme")
                ColumnLayout {
                    spacing: 2
                    CheckBox { id: grid; text: qsTr("Gitternetz anzeigen") }
                    CheckBox { id: legend; text: qsTr("Legende im Diagrammkopf") }
                    CheckBox { id: cursor; text: qsTr("Fadenkreuz mit Wertanzeige (2D)") }
                    CheckBox { id: smooth; text: qsTr("Kantenglättung · braucht mehr Grafikleistung") }
                }
            }

            FormSection {
                title: qsTr("Live-Anzeige")
                FieldRow {
                    label: qsTr("Aktualisierung")
                    labelWidth: 150
                    ComboBox { id: rate; Layout.preferredWidth: 200; model: ["16 ms · bis zu 60 Hz", "33 ms · bis zu 30 Hz", "50 ms · bis zu 20 Hz", "100 ms · bis zu 10 Hz", "200 ms · bis zu 5 Hz"]; Accessible.name: qsTr("Aktualisierungsintervall") }
                }
                FieldRow {
                    label: qsTr("Punkte pro Kurve")
                    labelWidth: 150
                    hint: qsTr("Nur die Anzeige; der Rohpuffer ist davon unabhängig.")
                    SpinBox { id: pointLimit; from: 500; to: 50000; stepSize: 500; editable: true; Layout.preferredWidth: 130; Accessible.name: qsTr("Punkte pro 2D-Kurve") }
                }
            }

            FormSection {
                title: qsTr("Verdichtung")
                CheckBox { id: reduction; text: qsTr("Y-Daten ohne explizites X für die Anzeige verdichten") }
                FieldRow {
                    enabled: reduction.checked
                    label: qsTr("Zielwerte pro Sekunde")
                    labelWidth: 150
                    hint: qsTr("Lokale Minima und Maxima bleiben erhalten. Statistik und CSV nutzen immer die Rohdaten.")
                    SpinBox { id: targetRate; from: 10; to: 5000; stepSize: 10; editable: true; Layout.preferredWidth: 130; Accessible.name: qsTr("Zielwerte pro Sekunde") }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: note.implicitHeight + 20
                radius: AppTheme.radius.large
                color: AppTheme.surfaces.panel
                border.color: AppTheme.borders.primary
                RowLayout {
                    id: note
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    Icon { name: "info"; color: AppTheme.text.hint; Layout.alignment: Qt.AlignTop }
                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        color: AppTheme.text.secondary
                        font.pixelSize: AppTheme.fontSize.small
                        text: qsTr("Speichergrenzen: bis zu 20.000 Rohwerte pro Signal, insgesamt 250.000. Bei Überlast werden alte Werte verworfen und in der Statusleiste gemeldet – kein verlustfreier Langzeitrekorder.")
                    }
                }
            }
            Item { implicitHeight: 4 }
        }
    }

    footer: DialogFooter {
        Item { Layout.fillWidth: true }
        UiButton { text: qsTr("Abbrechen"); onClicked: root.reject() }
        UiButton { text: qsTr("Übernehmen"); variant: "primary"; onClicked: if (root.apply()) root.accept() }
    }
}

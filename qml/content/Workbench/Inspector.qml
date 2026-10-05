// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import QtQuick.Dialogs
import Theme 1.0

/**
 * Right column. Shows the selected signal if there is one, otherwise the active
 * chart. A view over the workspace controller, never a second state owner.
 */
Rectangle {
    id: root
    property var workspaceController
    property var backend
    property string selectedSignalId: ""
    property var statistics: ({})
    signal exportSignalRequested(string uniqueId)
    signal exportImageRequested(string chartId)

    readonly property var wc: workspaceController
    readonly property string chartId: wc ? wc.activeChartId : ""
    readonly property var chart: {
        var charts = wc ? wc.availableCharts : []
        for (var i = 0; i < charts.length; i++) if (charts[i].chartId === chartId) return charts[i]
        return null
    }
    readonly property var chartWindow: wc && chart && wc.registeredWindowCount >= 0 ? wc.windowForChart(chartId) : null
    readonly property var renderer: chartWindow ? chartWindow.chartRenderer : null
    readonly property bool isTimeSeries: !!chart && chart.chartType === "time_series"
    readonly property var signalEntry: wc && selectedSignalId && wc.signalModel.count >= 0 ? wc.signalModel.getSignal(selectedSignalId) : null
    readonly property string mode: signalEntry ? "signal" : chart ? "chart" : "none"
    readonly property int usageCount: {
        if (!wc || !selectedSignalId || wc.assignmentRevision < 0) return 0
        var n = 0
        for (var i = 0; i < wc.availableCharts.length; i++)
            if (wc.chartLineModel.hasLineForChart(selectedSignalId, wc.availableCharts[i].chartId, null)
                || wc.chartLineModel.hasLineForChart(selectedSignalId, wc.availableCharts[i].chartId, "y")
                || wc.chartLineModel.hasLineForChart(selectedSignalId, wc.availableCharts[i].chartId, "x")) n++
        return n
    }

    color: AppTheme.surfaces.panel

    function pollStatistics() {
        statistics = backend && selectedSignalId && backend.get_signal_statistics ? backend.get_signal_statistics(selectedSignalId) : ({})
    }
    function number(key, digits) {
        var value = statistics[key]
        if (value === undefined || value === null || !isFinite(value)) return "–"
        return (digits === 0 ? Math.round(value).toLocaleString(Qt.locale("de_DE"), "f", 0) : Number(value).toPrecision(digits || 6)).replace("-", "−")
    }
    function compact(value) { return String(Number(Number(value).toPrecision(6))) }
    function loadViewRange() {
        rangeError.text = ""
        if (!renderer || !renderer.viewSettings) return
        var v = renderer.viewSettings()
        xMin.text = compact(v.xMin); xMax.text = compact(v.xMax)
        yMin.text = compact(v.yMin); yMax.text = compact(v.yMax)
        if (v.timeWindow !== undefined) windowSeconds.value = Math.round(v.timeWindow)
    }
    function applyViewRange() {
        var values = [xMin.text, xMax.text, yMin.text, yMax.text].map(function(t) { return Number(String(t).replace("−", "-").replace(",", ".")) })
        if (!values.every(isFinite) || values[0] >= values[1] || values[2] >= values[3]) {
            rangeError.text = qsTr("Endliche Zahlen eingeben; Minimum muss kleiner als Maximum sein.")
            return
        }
        rangeError.text = ""
        renderer.setViewRange(values[0], values[1], values[2], values[3])
    }

    onSelectedSignalIdChanged: pollStatistics()
    onChartIdChanged: { selectedSignalId = ""; Qt.callLater(loadViewRange) }
    onRendererChanged: Qt.callLater(loadViewRange)
    Connections {
        target: root.wc
        function onChartActivated() { root.selectedSignalId = "" }
    }
    Connections {
        target: root.wc
        function onChartActivated() { root.selectedSignalId = "" }
    }
    Timer { interval: 1000; running: root.mode === "signal" && root.visible; repeat: true; onTriggered: root.pollStatistics() }

    Rectangle { anchors.left: parent.left; width: 1; height: parent.height; color: AppTheme.borders.primary }

    component Section: ColumnLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 14
        Layout.bottomMargin: 14
        spacing: 8
    }
    component Divider: Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: AppTheme.borders.primary }
    component StatTile: Rectangle {
        property string label
        property string value
        Layout.fillWidth: true
        implicitHeight: 50
        radius: AppTheme.radius.medium
        color: AppTheme.surfaces.background
        border.color: AppTheme.borders.subtle
        Accessible.role: Accessible.StaticText
        Accessible.name: label + ": " + value
        Column {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 2
            Label { text: parent.parent.label; font.pixelSize: AppTheme.fontSize.caption; color: AppTheme.text.hint }
            Label { text: parent.parent.value; font.family: AppTheme.monoFamily; font.pixelSize: 14 }
        }
    }

    // ---------------------------------------------------------------- none
    ColumnLayout {
        visible: root.mode === "none"
        anchors.centerIn: parent
        width: parent.width - 48
        spacing: 8
        Label { text: qsTr("Nichts ausgewählt"); font.weight: Font.DemiBold; Layout.alignment: Qt.AlignHCenter }
        Label {
            text: qsTr("Ein Diagramm anklicken, um Kurven und Achsen einzustellen, oder links ein Signal wählen.")
            wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; color: AppTheme.text.secondary; Layout.fillWidth: true
        }
    }

    // ---------------------------------------------------------------- chart
    ColumnLayout {
        visible: root.mode === "chart"
        anchors.fill: parent
        anchors.leftMargin: 1
        spacing: 0

        Section {
            Caption { text: qsTr("Diagramm") }
            RowLayout {
                Layout.fillWidth: true
                TextField {
                    id: chartTitleField
                    Layout.fillWidth: true
                    text: root.chart ? root.chart.chartTitle : ""
                    font.pixelSize: AppTheme.fontSize.large
                    font.weight: Font.DemiBold
                    maximumLength: 100
                    selectByMouse: true
                    Accessible.name: qsTr("Diagrammname")
                    background: Rectangle {
                        radius: AppTheme.radius.medium
                        color: chartTitleField.activeFocus ? AppTheme.surfaces.background : "transparent"
                        border.color: chartTitleField.activeFocus ? AppTheme.borders.focus : chartTitleField.hovered ? AppTheme.borders.strong : "transparent"
                    }
                    onEditingFinished: if (text.trim() && root.chart && text.trim() !== root.chart.chartTitle) root.wc.renameChart(root.chartId, text.trim())
                }
            }
            Label {
                text: root.chart ? AppTheme.chartTypeName(root.chart.chartType) + (root.isTimeSeries ? qsTr(" · Zeit auf der X-Achse") : qsTr(" · X und Y aus dem Datenpaket")) : ""
                font.pixelSize: AppTheme.fontSize.small
                color: AppTheme.text.secondary
            }
        }
        Divider {}

        ScrollView {
            id: chartScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                width: chartScroll.availableWidth
                spacing: 0

                Section {
                    RowLayout {
                        Caption { text: qsTr("Kurven"); Layout.fillWidth: true }
                        Label { text: curveList.visibleCount; font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.hint }
                    }
                    Column {
                        id: curveList
                        Layout.fillWidth: true
                        property int visibleCount: {
                            var n = 0
                            var lines = root.wc ? root.wc.chartLineModel : null
                            if (!lines || root.wc.assignmentRevision < 0) return 0
                            for (var i = 0; i < lines.count; i++) if (lines.get(i).chartId === root.chartId) n++
                            return n
                        }
                        Repeater {
                            model: root.wc ? root.wc.chartLineModel : null
                            delegate: RowLayout {
                                id: curve
                                required property var model
                                readonly property bool mine: model.chartId === root.chartId
                                width: curveList.width
                                height: mine ? 32 : 0
                                visible: mine
                                spacing: 8
                                CheckBox {
                                    checked: curve.model.visible
                                    padding: 0
                                    Accessible.name: qsTr("Sichtbar: ") + curve.model.displayName
                                    onToggled: root.wc.setLineVisibility(curve.model.lineKey, checked)
                                }
                                Rectangle { width: 14; height: 14; radius: 3; color: curve.model.color }
                                Label { text: curve.model.displayName; elide: Text.ElideRight; Layout.fillWidth: true }
                                Label {
                                    text: curve.model.valueField ? curve.model.valueField.toUpperCase() + "(t)" : AppTheme.chartTypeBadge(root.chart ? root.chart.chartType : "")
                                    font.family: AppTheme.monoFamily
                                    font.pixelSize: AppTheme.fontSize.small
                                    color: AppTheme.text.secondary
                                }
                                IconButton {
                                    iconName: "close"; tip: qsTr("Aus Diagramm entfernen")
                                    implicitWidth: 24; implicitHeight: 24
                                    onClicked: root.wc.removeChartLine(curve.model.lineKey)
                                }
                            }
                        }
                    }
                    Label {
                        visible: curveList.visibleCount === 0
                        text: qsTr("Signal von links auf das Diagramm ziehen oder hier hinzufügen.")
                        wrapMode: Text.WordWrap; color: AppTheme.text.hint; Layout.fillWidth: true
                    }
                    UiButton {
                        text: qsTr("Signal hinzufügen")
                        iconName: "plus"
                        variant: "ghost"
                        Layout.fillWidth: true
                        enabled: root.wc && root.wc.signalModel.count > 0
                        onClicked: addMenu.popup()
                        Menu {
                            id: addMenu
                            // Instantiator, not Repeater: Menu only adopts items inserted through its API.
                            Instantiator {
                                model: root.wc ? root.wc.signalModel : null
                                delegate: MenuItem {
                                    id: pick
                                    required property string uniqueId
                                    required property string displayName
                                    required property var color
                                    readonly property bool onChart: root.wc.assignmentRevision >= 0 && root.wc.hasAssignedSignal(root.chartId, uniqueId)
                                    text: displayName
                                    enabled: !onChart
                                    onTriggered: root.wc.assignSignal(uniqueId, root.chartId, root.isTimeSeries ? "y" : null)
                                    contentItem: RowLayout {
                                        spacing: 8
                                        Rectangle { implicitWidth: 10; implicitHeight: 10; radius: 2; color: pick.color }
                                        Label { text: pick.displayName; elide: Text.ElideRight; Layout.fillWidth: true; color: pick.enabled ? AppTheme.text.primary : AppTheme.text.disabled }
                                        Label { visible: pick.onChart; text: qsTr("bereits drin"); font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.hint }
                                    }
                                }
                                onObjectAdded: function(index, object) { addMenu.insertItem(index, object) }
                                onObjectRemoved: function(index, object) { addMenu.removeItem(object) }
                            }
                        }
                    }
                }
                Divider {}

                Section {
                    visible: !!root.renderer && !!root.renderer.viewSettings
                    Caption { text: qsTr("Achsen") }
                    RowLayout {
                        visible: root.isTimeSeries
                        Layout.fillWidth: true
                        spacing: 8
                        Label { text: qsTr("Zeit"); color: AppTheme.text.secondary; Layout.preferredWidth: 56 }
                        Segmented {
                            accessibleName: qsTr("Zeitachse")
                            options: [{ text: qsTr("Folgen") }, { text: qsTr("Fest") }]
                            currentIndex: root.renderer && root.renderer.autoScroll ? 0 : 1
                            onActivated: function(index) { if ((index === 0) !== root.renderer.autoScroll) root.renderer.toggleAutoScroll() }
                        }
                        Item { Layout.fillWidth: true }
                        SpinBox {
                            id: windowSeconds
                            from: 1; to: 86400; editable: true
                            implicitWidth: 92
                            Accessible.name: qsTr("Zeitfenster in Sekunden")
                            onValueModified: if (root.renderer && root.renderer.setTimeWindow) root.renderer.setTimeWindow(value)
                        }
                        Label { text: "s"; color: AppTheme.text.hint }
                    }
                    RowLayout {
                        visible: root.isTimeSeries
                        Layout.fillWidth: true
                        spacing: 8
                        Label { text: "Y"; color: AppTheme.text.secondary; Layout.preferredWidth: 56 }
                        Segmented {
                            accessibleName: qsTr("Y-Achse")
                            options: [{ text: qsTr("Auto") }, { text: qsTr("Manuell") }]
                            currentIndex: root.renderer && root.renderer.autoScaleY === false ? 1 : 0
                            onActivated: function(index) {
                                root.renderer.autoScaleY = index === 0
                                if (index === 0) root.renderer.scheduleYAxisUpdate()
                                else root.loadViewRange()
                            }
                        }
                    }
                    Label { text: qsTr("Ausschnitt"); color: AppTheme.text.secondary; Layout.topMargin: 4 }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 3
                        columnSpacing: 8
                        rowSpacing: 6
                        Label { text: root.isTimeSeries ? "t (s)" : "X"; color: AppTheme.text.hint; Layout.preferredWidth: 40 }
                        TextField { id: xMin; Layout.fillWidth: true; font.family: AppTheme.monoFamily; Accessible.name: qsTr("X Minimum"); selectByMouse: true }
                        TextField { id: xMax; Layout.fillWidth: true; font.family: AppTheme.monoFamily; Accessible.name: qsTr("X Maximum"); selectByMouse: true }
                        Label { text: "Y"; color: AppTheme.text.hint }
                        TextField { id: yMin; Layout.fillWidth: true; font.family: AppTheme.monoFamily; Accessible.name: qsTr("Y Minimum"); selectByMouse: true }
                        TextField { id: yMax; Layout.fillWidth: true; font.family: AppTheme.monoFamily; Accessible.name: qsTr("Y Maximum"); selectByMouse: true }
                    }
                    Label { id: rangeError; visible: text !== ""; color: "#F29C99"; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.pixelSize: AppTheme.fontSize.small }
                    RowLayout {
                        Layout.fillWidth: true
                        UiButton { text: qsTr("Aktuell übernehmen"); variant: "ghost"; onClicked: root.loadViewRange() }
                        Item { Layout.fillWidth: true }
                        UiButton { text: qsTr("Anwenden"); onClicked: root.applyViewRange() }
                    }
                    Label {
                        text: qsTr("Mausrad zoomt · Umschalt: nur X · Strg: nur Y · Ziehen verschiebt · Doppelklick passt ein")
                        wrapMode: Text.WordWrap; color: AppTheme.text.hint; font.pixelSize: AppTheme.fontSize.small; Layout.fillWidth: true
                    }
                }
                Divider { visible: !!root.renderer && !!root.renderer.viewSettings }

                Section {
                    Caption { text: qsTr("Anzeige · alle Diagramme") }
                    CheckBox { text: qsTr("Gitternetz"); checked: AppTheme.showGrid; padding: 0; onToggled: AppTheme.showGrid = checked }
                    CheckBox { text: qsTr("Legende im Diagrammkopf"); checked: AppTheme.showLegend; padding: 0; onToggled: AppTheme.showLegend = checked }
                    CheckBox { text: qsTr("Fadenkreuz mit Wertanzeige"); checked: AppTheme.showCrosshair; padding: 0; onToggled: AppTheme.showCrosshair = checked }
                }
            }
        }

        Divider {}
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 12
            spacing: 8
            UiButton { text: qsTr("Als PNG"); iconName: "image"; Layout.fillWidth: true; onClicked: root.exportImageRequested(root.chartId) }
            UiButton { text: qsTr("Schließen"); variant: "danger"; onClicked: root.wc.removeChart(root.chartId) }
        }
    }

    // ---------------------------------------------------------------- signal
    ColumnLayout {
        visible: root.mode === "signal"
        anchors.fill: parent
        anchors.leftMargin: 1
        spacing: 0

        Section {
            RowLayout {
                Caption { text: qsTr("Signal"); Layout.fillWidth: true }
                IconButton { iconName: "close"; tip: qsTr("Zurück zum Diagramm"); onClicked: root.selectedSignalId = "" }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                AbstractButton {
                    implicitWidth: 22; implicitHeight: 22
                    Accessible.name: qsTr("Farbe ändern")
                    ToolTip.visible: hovered; ToolTip.text: qsTr("Farbe ändern")
                    hoverEnabled: true
                    onClicked: { colorDialog.selectedColor = root.signalEntry.color; colorDialog.open() }
                    background: Rectangle { radius: 4; color: root.signalEntry ? root.signalEntry.color : "transparent"; border.color: parent.visualFocus ? AppTheme.borders.focus : AppTheme.borders.strong; border.width: parent.visualFocus ? 2 : 1 }
                }
                TextField {
                    id: signalNameField
                    Layout.fillWidth: true
                    text: root.signalEntry ? root.signalEntry.displayName : ""
                    font.pixelSize: AppTheme.fontSize.large
                    font.weight: Font.DemiBold
                    maximumLength: 100
                    selectByMouse: true
                    Accessible.name: qsTr("Signalname")
                    background: Rectangle {
                        radius: AppTheme.radius.medium
                        color: signalNameField.activeFocus ? AppTheme.surfaces.background : "transparent"
                        border.color: signalNameField.activeFocus ? AppTheme.borders.focus : signalNameField.hovered ? AppTheme.borders.strong : "transparent"
                    }
                    onEditingFinished: if (root.signalEntry && text.trim() && text.trim() !== root.signalEntry.displayName)
                        root.wc.updateSignalById(root.selectedSignalId, text.trim(), root.signalEntry.color)
                }
            }
            Label {
                text: root.signalEntry ? root.signalEntry.interfaceType + " · ID " + root.signalEntry.dataId : ""
                font.family: AppTheme.monoFamily
                font.pixelSize: AppTheme.fontSize.small
                color: AppTheme.text.secondary
            }
        }
        Divider {}

        ScrollView {
            id: signalScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                width: signalScroll.availableWidth
                spacing: 0

                Section {
                    RowLayout {
                        Caption { text: qsTr("In Diagrammen"); Layout.fillWidth: true }
                        Label {
                            text: qsTr("%1 von %2").arg(root.usageCount).arg(root.wc ? root.wc.availableCharts.length : 0)
                            font.pixelSize: AppTheme.fontSize.small
                            color: AppTheme.text.hint
                        }
                    }
                    Label {
                        visible: !root.wc || root.wc.availableCharts.length === 0
                        text: qsTr("Noch kein Diagramm vorhanden.")
                        color: AppTheme.text.hint
                    }
                    Repeater {
                        model: root.wc ? root.wc.availableCharts : []
                        delegate: Rectangle {
                            id: usage
                            required property var modelData
                            readonly property bool ts: modelData.chartType === "time_series"
                            readonly property bool used: assigned(ts ? "y" : null) || (ts && assigned("x"))
                            function assigned(field) {
                                return root.wc.assignmentRevision >= 0 && root.wc.chartLineModel.hasLineForChart(root.selectedSignalId, modelData.chartId, field)
                            }
                            function toggle(field, on) {
                                if (on) root.wc.assignSignal(root.selectedSignalId, modelData.chartId, field)
                                else root.wc.unassignSignal(root.selectedSignalId, modelData.chartId, field)
                            }
                            Layout.fillWidth: true
                            implicitHeight: 40
                            radius: AppTheme.radius.medium
                            color: used ? AppTheme.surfaces.card : "transparent"
                            border.color: used ? AppTheme.borders.strong : AppTheme.borders.primary
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 8
                                spacing: 8
                                Rectangle {
                                    readonly property var colors: AppTheme.chartTypeBadgeColors(usage.modelData.chartType)
                                    implicitWidth: badge.implicitWidth + 10
                                    implicitHeight: 18
                                    radius: 4
                                    color: colors[0]
                                    Label { id: badge; anchors.centerIn: parent; text: AppTheme.chartTypeBadge(usage.modelData.chartType); color: parent.colors[1]; font.family: AppTheme.monoFamily; font.pixelSize: AppTheme.fontSize.caption }
                                }
                                Label {
                                    text: usage.modelData.chartTitle
                                    elide: Text.ElideRight
                                    color: usage.used ? AppTheme.text.primary : AppTheme.text.secondary
                                    Layout.fillWidth: true
                                }
                                ToggleChip {
                                    text: usage.ts ? "Y(t)" : qsTr("Zeigen")
                                    mono: usage.ts
                                    checked: usage.assigned(usage.ts ? "y" : null)
                                    onToggled: usage.toggle(usage.ts ? "y" : null, checked)
                                    Accessible.name: usage.modelData.chartTitle + " " + text
                                    ToolTip.visible: hovered
                                    ToolTip.delay: 500
                                    ToolTip.text: usage.ts ? qsTr("Messwert über der Zeit") : qsTr("In diesem Diagramm anzeigen")
                                }
                                ToggleChip {
                                    visible: usage.ts
                                    text: "X(t)"
                                    checked: usage.ts && usage.assigned("x")
                                    onToggled: usage.toggle("x", checked)
                                    Accessible.name: usage.modelData.chartTitle + " X(t)"
                                    ToolTip.visible: hovered
                                    ToolTip.delay: 500
                                    ToolTip.text: qsTr("X-Wert über der Zeit; nur bei explizitem X im Datenpaket")
                                }
                            }
                        }
                    }
                }
                Divider {}

                Section {
                    Caption { text: qsTr("Statistik · Rohpuffer") }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 8
                        rowSpacing: 8
                        StatTile { label: qsTr("Letzter Wert"); value: root.number("latest") }
                        StatTile { label: qsTr("Werte im Puffer"); value: root.number("count", 0) }
                        StatTile { label: qsTr("Minimum"); value: root.number("min") }
                        StatTile { label: qsTr("Maximum"); value: root.number("max") }
                        StatTile { label: qsTr("Mittelwert"); value: root.number("mean") }
                        StatTile { label: qsTr("RMS"); value: root.number("rms") }
                        StatTile { label: qsTr("Std.-Abweichung"); value: root.number("stddev") }
                        StatTile { label: qsTr("Zeitspanne (s)"); value: root.number("duration", 5) }
                    }
                    Label {
                        text: qsTr("Rohwerte ohne Verdichtung. CSV enthält zusätzlich X, Z, Quellzeit und Empfangszeit.")
                        wrapMode: Text.WordWrap; color: AppTheme.text.hint; font.pixelSize: AppTheme.fontSize.small; Layout.fillWidth: true
                    }
                }
            }
        }

        Divider {}
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 12
            spacing: 8
            UiButton {
                text: qsTr("Signal als CSV"); iconName: "download"; Layout.fillWidth: true
                enabled: (root.statistics.count || 0) > 0
                onClicked: root.exportSignalRequested(root.selectedSignalId)
            }
            UiButton { text: qsTr("Entfernen"); variant: "danger"; onClicked: removeConfirm.open() }
        }
    }

    ColorDialog {
        id: colorDialog
        title: qsTr("Signalfarbe wählen")
        onAccepted: root.wc.updateSignalById(root.selectedSignalId, root.signalEntry.displayName, selectedColor.toString())
    }
    ConfirmDialog {
        id: removeConfirm
        title: qsTr("Signal entfernen?")
        text: qsTr("Das Signal wird aus allen Diagrammen entfernt, sein Rohpuffer wird geleert und neue Werte werden verworfen. Vorher benötigte Daten als CSV exportieren.")
        onAccepted: { root.wc.removeSignal(root.selectedSignalId); root.selectedSignalId = "" }
    }
}

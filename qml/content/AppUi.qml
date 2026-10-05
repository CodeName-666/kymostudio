// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Window 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import QtQuick.Dialogs
import QtCore
import Common 1.0
import Theme 1.0
import "Workspace"
import "Workbench"

/**
 * Desktop workbench: sources left, charts centre, context inspector right.
 * Acquisition (sources) and display (live/paused) are separate, always visible states.
 */
ApplicationWindow {
    id: applicationWindow
    objectName: "applicationWindow"
    width: Math.min(uiState.windowWidth, Screen.width)
    height: Math.min(uiState.windowHeight, Screen.height)
    minimumWidth: 1024
    minimumHeight: 640
    visible: true
    title: qsTr("KymoStudio · Datenanalyse")
    color: AppTheme.surfaces.background
    font.family: AppTheme.fontFamily
    font.pixelSize: AppTheme.fontSize.medium

    palette.window: AppTheme.surfaces.dialog
    palette.windowText: AppTheme.text.primary
    // Fusion fills inputs and check boxes with base and outlines with window.darker():
    // base must stay distinguishable from the panels.
    palette.base: "#1A212B"
    palette.alternateBase: AppTheme.surfaces.panel
    palette.text: AppTheme.text.primary
    palette.button: AppTheme.surfaces.control
    palette.buttonText: AppTheme.text.primary
    palette.highlight: AppTheme.palette.primary
    palette.highlightedText: AppTheme.palette.primaryText
    palette.placeholderText: AppTheme.text.placeholder
    palette.light: "#2A3340"
    palette.midlight: "#222A35"
    palette.mid: AppTheme.borders.strong
    palette.dark: AppTheme.borders.primary
    palette.shadow: "#000000"
    palette.toolTipBase: AppTheme.surfaces.control
    palette.toolTipText: AppTheme.text.primary
    palette.link: AppTheme.palette.primary

    property var appController
    property var workspaceController
    property bool uiReady: false
    property bool displayPaused: false
    property bool sidebarsVisible: uiState.sidebarsVisible
    property var diagnostics: ({})
    property var connectionList: []
    property int frameIntervalMs: 33
    property string statusText: qsTr("Bereit.")
    property string statusLevel: "info"
    property string exportSignalId: ""
    property string exportImageChartId: ""
    property string demoConnectionId: ""
    property alias chartWorkspace: chartWorkspace
    property alias settingsPopup: preferences
    property alias toolbar: topBar

    readonly property int connectedCount: connectionList.filter(function(c) { return c.status === "connected" }).length
    readonly property int connectingCount: connectionList.filter(function(c) { return c.status === "connecting" }).length
    readonly property int errorCount: connectionList.filter(function(c) { return c.status === "error" }).length
    readonly property bool acquiring: connectedCount + connectingCount > 0
    readonly property int losses: (diagnostics.ingressDropped || 0) + (diagnostics.displayDropped || 0) + (diagnostics.eventDropped || 0) + (diagnostics.signalLimitDropped || 0)
    readonly property int bufferLimit: 250000
    readonly property real bufferFill: Math.min(1, (diagnostics.retained || 0) / bufferLimit)
    readonly property int chartCount: workspaceController ? workspaceController.chartModel.count : 0

    Settings {
        id: uiState
        category: "workbench-v3"
        property int windowWidth: 1440
        property int windowHeight: 900
        property int sourcesWidth: 280
        property int inspectorWidth: 320
        property bool sidebarsVisible: true
        property string layoutMode: "tile"
        property bool grid: true
        property bool legend: true
        property bool crosshair: true
        property bool smoothing: false
    }

    function initializeWorkbench() {
        AppTheme.showGrid = uiState.grid; AppTheme.showLegend = uiState.legend
        AppTheme.showCrosshair = uiState.crosshair; AppTheme.antialiasing = uiState.smoothing
        var performance = Backend.get_performance_settings()
        AppTheme.displayPointLimit = performance.display_points_per_signal
        frameIntervalMs = performance.frame_interval_ms
        workspaceController.layoutMode = uiState.layoutMode
        workspaceController.restoreSnapshot(Backend.get_workspace())
        uiReady = true
        refreshDiagnostics()
        scheduleLayout()
    }
    function rememberPreferences() {
        uiState.grid = AppTheme.showGrid; uiState.legend = AppTheme.showLegend
        uiState.crosshair = AppTheme.showCrosshair; uiState.smoothing = AppTheme.antialiasing
        frameIntervalMs = Backend.get_performance_settings().frame_interval_ms
    }
    function refreshConnections() { connectionList = Backend.get_connections() }
    function refreshDiagnostics() {
        if (!uiReady) return
        diagnostics = Backend.get_diagnostics()
        refreshConnections()
    }
    function setDisplayPaused(paused) {
        displayPaused = paused
        Backend.set_display_paused(paused)
        showStatusMessage("info", paused ? qsTr("Anzeige pausiert. Erfassung und Rohdatenpuffer laufen weiter.") : qsTr("Live-Anzeige fortgesetzt."))
    }
    function showStatusMessage(level, message) { statusLevel = level; statusText = message }
    function saveWorkspace() {
        var saved = workspaceController ? Backend.save_workspace(workspaceController.snapshot()) : false
        rememberPreferences()
        return saved
    }
    function openChartCreation() { chartCreation.open() }
    function startAll() {
        for (var i = 0; i < connectionList.length; i++)
            if (connectionList[i].status !== "connected" && connectionList[i].status !== "connecting") Backend.start_connection(connectionList[i].id)
    }
    function stopAll() {
        for (var i = 0; i < connectionList.length; i++)
            if (connectionList[i].status === "connected" || connectionList[i].status === "connecting") Backend.stop_connection(connectionList[i].id)
    }
    function startDemo() {
        if (demoConnectionId && Backend.get_connection_details(demoConnectionId).id) {
            Backend.start_connection(demoConnectionId)
            return
        }
        var chartId = workspaceController.createChart("time_series", qsTr("Demo · drei Signale"))
        if (!chartId) return
        demoConnectionId = Backend.create_connection("Test", "Demo", {type: "Multi", sample_ms: 20, use_timestamp: true})
        if (!demoConnectionId) return
        var names = ["Sinus", "Kosinus", "Sinus · 2×"]
        for (var i = 0; i < 3; i++) {
            var uniqueId = demoConnectionId + "_" + i
            workspaceController.addSignal(uniqueId, names[i], AppTheme.seriesColors[i], "Test", i, {})
            workspaceController.setSignalCharts(uniqueId, [{chartId: chartId, chartType: "time_series", valueField: "y"}])
        }
        workspaceController.bringToFront(chartId)
        Backend.start_connection(demoConnectionId)
        refreshConnections()
    }
    function createChartWithSignals(type, title, signalIds) {
        var chartId = workspaceController.createChart(type, title)
        if (!chartId) return
        for (var i = 0; i < signalIds.length; i++)
            workspaceController.assignSignal(signalIds[i], chartId, type === "time_series" ? "y" : null)
        workspaceController.bringToFront(chartId)
        scheduleLayout()
    }

    // Layout: "tile" arranges all charts, "focus" maximizes the active one, "free" keeps user geometry.
    function scheduleLayout() { layoutTimer.restart() }
    function applyLayout() {
        var wc = workspaceController
        if (!wc || !chartCount) return
        if (wc.layoutMode === "tile") {
            wc.tileCharts(chartWorkspace.width, chartWorkspace.height)
        } else if (wc.layoutMode === "focus") {
            wc.focusChart(wc.activeChartId || wc.chartModel.get(0).chartId)
        } else {
            for (var i = 0; i < wc.chartModel.count; i++) {
                var window = wc.windowForChart(wc.chartModel.get(i).chartId)
                if (window && window.isMaximized) window.toggleMaximize()
            }
        }
    }
    Timer { id: layoutTimer; interval: 60; onTriggered: applyLayout() }
    Connections {
        target: applicationWindow.workspaceController
        function onLayoutModeChanged() { uiState.layoutMode = applicationWindow.workspaceController.layoutMode; applicationWindow.scheduleLayout() }
        function onActiveChartIdChanged() { if (applicationWindow.workspaceController.layoutMode === "focus") applicationWindow.scheduleLayout() }
        function onRegisteredWindowCountChanged() { applicationWindow.scheduleLayout() }
    }
    Connections {
        target: Backend
        ignoreUnknownSignals: true
        function onConnections_changed() { applicationWindow.refreshConnections() }
        function onConnection_status_changed() { applicationWindow.refreshConnections() }
    }

    component Divider: Rectangle { implicitWidth: 1; implicitHeight: 20; color: AppTheme.borders.primary }
    component StatusDot: Rectangle {
        property string state: "idle"
        width: 8; height: 8; radius: 4
        color: state === "connecting" ? "transparent" : state === "live" ? AppTheme.palette.success : state === "error" ? AppTheme.palette.danger : AppTheme.palette.idle
        border.width: state === "connecting" ? 2 : 0
        border.color: AppTheme.palette.warning
    }

    header: Rectangle {
        id: topBar
        implicitHeight: AppTheme.heights.header
        color: AppTheme.surfaces.panel
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: AppTheme.borders.primary }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 12
            spacing: 12

            Row {
                spacing: 8
                Icon { name: "logo"; size: 20; color: AppTheme.palette.primary; anchors.verticalCenter: parent.verticalCenter }
                Label { text: "KymoStudio"; font.pixelSize: 14; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
            }
            Divider {}

            UiButton {
                id: acquisitionPill
                readonly property var tone: applicationWindow.errorCount ? AppTheme.tone.danger
                    : applicationWindow.connectedCount ? AppTheme.tone.live
                    : applicationWindow.connectingCount ? AppTheme.tone.warning : AppTheme.tone.neutral
                text: applicationWindow.errorCount ? qsTr("Fehler · %1 Quelle(n)").arg(applicationWindow.errorCount)
                    : applicationWindow.connectedCount ? qsTr("Erfassung läuft · %1 von %2 Quellen").arg(applicationWindow.connectedCount).arg(applicationWindow.connectionList.length)
                    : applicationWindow.connectingCount ? qsTr("Verbindet …")
                    : qsTr("Keine Erfassung")
                toneBackground: tone.bg
                toneBorder: tone.border
                toneText: tone.text
                leftPadding: 26
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Quellen verwalten")
                onClicked: sourcesDialog.openFor("")
                StatusDot {
                    x: 12; anchors.verticalCenter: parent.verticalCenter
                    state: applicationWindow.errorCount ? "error" : applicationWindow.connectedCount ? "live" : applicationWindow.connectingCount ? "connecting" : "idle"
                }
            }
            UiButton {
                text: applicationWindow.acquiring ? qsTr("Stoppen") : qsTr("Starten")
                iconName: applicationWindow.acquiring ? "stop" : "play"
                enabled: applicationWindow.connectionList.length > 0
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: applicationWindow.acquiring ? qsTr("Alle laufenden Quellen stoppen") : qsTr("Alle Quellen starten")
                onClicked: applicationWindow.acquiring ? applicationWindow.stopAll() : applicationWindow.startAll()
            }

            Caption { text: qsTr("Anzeige"); Layout.leftMargin: 8 }
            Segmented {
                accessibleName: qsTr("Anzeige")
                options: [{ text: qsTr("Live"), icon: "play" }, { text: applicationWindow.displayPaused ? qsTr("Pausiert") : qsTr("Pausieren"), icon: "pause", tone: "warning" }]
                currentIndex: applicationWindow.displayPaused ? 1 : 0
                onActivated: function(index) { if ((index === 1) !== applicationWindow.displayPaused) applicationWindow.setDisplayPaused(index === 1) }
                ToolTip.visible: pauseHover.hovered
                ToolTip.delay: 600
                ToolTip.text: qsTr("Pausiert nur die Darstellung, nicht die Erfassung. Ctrl+Leertaste")
                HoverHandler { id: pauseHover }
            }

            Item { Layout.fillWidth: true }

            Segmented {
                accessibleName: qsTr("Anordnung der Diagramme")
                enabled: applicationWindow.chartCount > 0
                options: [{ text: qsTr("Kacheln"), icon: "tiles" }, { text: qsTr("Fokus"), icon: "focus" }, { text: qsTr("Frei"), icon: "free" }]
                currentIndex: ["tile", "focus", "free"].indexOf(applicationWindow.workspaceController ? applicationWindow.workspaceController.layoutMode : "tile")
                onActivated: function(index) { applicationWindow.workspaceController.layoutMode = ["tile", "focus", "free"][index] }
            }
            UiButton { text: qsTr("Diagramm"); iconName: "plus"; variant: "primary"; onClicked: chartCreation.open() }
            UiButton {
                id: exportButton
                text: qsTr("Export")
                iconName: "download"
                onClicked: exportMenu.popup(exportButton, 0, exportButton.height + 4)
                Menu {
                    id: exportMenu
                    MenuItem { text: qsTr("Alle Rohdaten als CSV …"); enabled: !applicationWindow.diagnostics.exporting; onTriggered: { applicationWindow.exportSignalId = ""; csvDialog.open() } }
                    MenuItem { text: qsTr("Arbeitsfläche als PNG …"); onTriggered: { applicationWindow.exportImageChartId = ""; imageDialog.open() } }
                    MenuSeparator {}
                    MenuItem { text: qsTr("Konfiguration exportieren …"); onTriggered: { applicationWindow.saveWorkspace(); configExportDialog.open() } }
                    MenuItem { text: qsTr("Konfiguration importieren …"); onTriggered: importConfirmation.open() }
                }
            }
            IconButton { iconName: "settings"; tip: qsTr("Darstellung & Leistung · Ctrl+,"); onClicked: preferences.open() }
            IconButton {
                id: moreButton
                iconName: "more"
                tip: qsTr("Weitere Aktionen")
                onClicked: moreMenu.popup(moreButton, 0, moreButton.height + 4)
                Menu {
                    id: moreMenu
                    MenuItem { text: qsTr("Demo starten"); onTriggered: applicationWindow.startDemo() }
                    MenuItem { text: qsTr("Alle Daten einpassen · Ctrl+0"); onTriggered: applicationWindow.workspaceController.fitAll() }
                    MenuItem { text: qsTr("Seitenleisten · Ctrl+B"); checkable: true; checked: applicationWindow.sidebarsVisible; onTriggered: applicationWindow.sidebarsVisible = !applicationWindow.sidebarsVisible }
                    MenuItem { text: qsTr("Layout speichern · Ctrl+S"); onTriggered: { if (applicationWindow.saveWorkspace()) applicationWindow.showStatusMessage("success", qsTr("Layout gespeichert.")) } }
                    MenuSeparator {}
                    MenuItem { text: qsTr("Messwerte leeren …"); onTriggered: clearConfirmation.open() }
                }
            }
        }
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal
        handle: Rectangle {
            implicitWidth: 4
            color: SplitHandle.pressed ? AppTheme.palette.primary : SplitHandle.hovered ? AppTheme.palette.primaryBorder : "transparent"
        }

        SourcesPanel {
            id: sourcesPanel
            objectName: "sourcesPanel"
            visible: applicationWindow.sidebarsVisible
            SplitView.preferredWidth: uiState.sourcesWidth
            SplitView.minimumWidth: 220
            SplitView.maximumWidth: 440
            workspaceController: applicationWindow.workspaceController
            backend: Backend
            dragGhost: dragGhost
            selectedSignalId: inspector.selectedSignalId
            onSignalSelected: function(uniqueId) { inspector.selectedSignalId = uniqueId }
            onSourceRequested: function(connectionId) { sourcesDialog.openFor(connectionId) }
            onAddSourceRequested: sourcesDialog.openNew()
            onAddSignalRequested: workspaceDialogs.openAddSignal()
        }

        ColumnLayout {
            SplitView.fillWidth: true
            SplitView.minimumWidth: 420
            spacing: 12

            Rectangle {
                visible: applicationWindow.displayPaused
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 12
                Layout.topMargin: 12
                implicitHeight: 40
                radius: AppTheme.radius.large
                color: AppTheme.tone.warning.bg
                border.color: AppTheme.tone.warning.border
                Accessible.role: Accessible.AlertMessage
                Accessible.name: qsTr("Anzeige pausiert")
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 8
                    spacing: 10
                    Icon { name: "pause"; color: AppTheme.tone.warning.text }
                    Label { text: qsTr("Anzeige pausiert"); font.weight: Font.Medium; color: AppTheme.tone.warning.text }
                    Label {
                        text: qsTr("Erfassung läuft weiter. Rohpuffer %1 %").arg(Math.round(applicationWindow.bufferFill * 100))
                            + (applicationWindow.bufferFill > 0.8 ? qsTr(" – älteste Werte werden bald ersetzt.") : ".")
                        color: "#D1B679"
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                    UiButton {
                        text: qsTr("Fortsetzen")
                        toneBackground: "#3A2E14"; toneBorder: "#6B5620"; toneText: AppTheme.tone.warning.text
                        onClicked: applicationWindow.setDisplayPaused(false)
                    }
                }
            }

            Item {
                id: chartWorkspace
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 12
                Layout.topMargin: applicationWindow.displayPaused ? 0 : 12
                clip: true
                onWidthChanged: applicationWindow.scheduleLayout()
                onHeightChanged: applicationWindow.scheduleLayout()

                ChartWorkspace { anchors.fill: parent; workspaceController: applicationWindow.workspaceController }

                // First start: three steps to the first plot.
                ColumnLayout {
                    visible: applicationWindow.chartCount === 0
                    anchors.centerIn: parent
                    width: Math.min(820, parent.width - 48)
                    spacing: 24
                    ColumnLayout {
                        spacing: 8
                        Label { text: qsTr("Messdaten in drei Schritten sichtbar machen"); font.pixelSize: 26; font.weight: Font.DemiBold; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        Label { text: qsTr("Ohne Hardware ausprobieren: Die Demo erzeugt drei Signale und ein vorbereitetes Zeitverlaufs-Diagramm."); color: AppTheme.text.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.pixelSize: 14 }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Repeater {
                            model: [
                                { title: qsTr("Quelle verbinden"), text: qsTr("Seriell, TCP, MQTT, CAN oder Testgenerator. Der Zustand erscheint oben und links."), action: qsTr("Quelle hinzufügen") },
                                { title: qsTr("Diagramm anlegen"), text: qsTr("Zeitverlauf für Messwert über Zeit, XY für echte X/Y-Paare aus dem Datenpaket."), action: qsTr("Diagramm erstellen") },
                                { title: qsTr("Signale zuordnen"), text: qsTr("Signal von links auf ein Diagramm ziehen. Die Ablagefläche zeigt, was möglich ist."), action: "" }
                            ]
                            delegate: Rectangle {
                                id: step
                                required property var modelData
                                required property int index
                                readonly property bool current: index === (applicationWindow.connectionList.length ? 1 : 0)
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                                Layout.fillHeight: true
                                implicitHeight: stepColumn.implicitHeight + 40
                                radius: 10
                                color: AppTheme.surfaces.panel
                                border.color: current ? AppTheme.palette.primaryBorder : AppTheme.borders.primary
                                ColumnLayout {
                                    id: stepColumn
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 10
                                    Rectangle {
                                        width: 26; height: 26; radius: 13
                                        color: "transparent"
                                        border.color: step.current ? AppTheme.palette.primary : AppTheme.borders.strong
                                        Label { anchors.centerIn: parent; text: step.index + 1; font.family: AppTheme.monoFamily; font.pixelSize: 12; color: step.current ? "#8FD0F6" : AppTheme.text.secondary }
                                    }
                                    Label { text: step.modelData.title; font.pixelSize: 15; font.weight: Font.DemiBold }
                                    Label { text: step.modelData.text; color: AppTheme.text.secondary; wrapMode: Text.WordWrap; Layout.fillWidth: true; lineHeight: 1.2 }
                                    Item { Layout.fillHeight: true }
                                    UiButton {
                                        visible: step.modelData.action !== ""
                                        text: step.modelData.action
                                        variant: step.current ? "primary" : "neutral"
                                        onClicked: step.index === 0 ? sourcesDialog.openNew() : chartCreation.open()
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16
                        UiButton { text: qsTr("Demo öffnen"); iconName: "play"; implicitHeight: 36; onClicked: applicationWindow.startDemo() }
                        Item { Layout.fillWidth: true }
                        Repeater {
                            model: [["Ctrl N", qsTr("Diagramm")], ["Ctrl Leer", qsTr("Anzeige pausieren")], ["Ctrl E", "CSV"]]
                            delegate: Row {
                                required property var modelData
                                spacing: 6
                                Label {
                                    text: modelData[0]; font.family: AppTheme.monoFamily; font.pixelSize: 11; color: AppTheme.text.label
                                    leftPadding: 6; rightPadding: 6; topPadding: 2; bottomPadding: 2
                                    background: Rectangle { radius: 4; color: AppTheme.surfaces.hover; border.color: AppTheme.borders.strong }
                                }
                                Label { text: modelData[1]; color: AppTheme.text.hint; anchors.verticalCenter: parent.verticalCenter }
                            }
                        }
                    }
                }
            }
        }

        Inspector {
            id: inspector
            objectName: "inspector"
            visible: applicationWindow.sidebarsVisible
            SplitView.preferredWidth: uiState.inspectorWidth
            SplitView.minimumWidth: 280
            SplitView.maximumWidth: 480
            workspaceController: applicationWindow.workspaceController
            backend: Backend
            onExportSignalRequested: function(uniqueId) { applicationWindow.exportSignalId = uniqueId; csvDialog.open() }
            onExportImageRequested: function(chartId) { applicationWindow.exportImageChartId = chartId; imageDialog.open() }
        }
    }

    footer: Rectangle {
        implicitHeight: AppTheme.heights.statusBar
        color: AppTheme.surfaces.panel
        Rectangle { width: parent.width; height: 1; color: AppTheme.borders.primary }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 16

            Row {
                spacing: 6
                StatusDot {
                    anchors.verticalCenter: parent.verticalCenter
                    state: applicationWindow.errorCount ? "error" : applicationWindow.connectedCount ? "live" : applicationWindow.connectingCount ? "connecting" : "idle"
                }
                Label {
                    text: applicationWindow.connectedCount ? qsTr("Erfassung läuft") : applicationWindow.connectingCount ? qsTr("Verbindet …") : qsTr("Keine Erfassung")
                    font.pixelSize: AppTheme.fontSize.small
                    color: applicationWindow.connectedCount ? AppTheme.tone.live.text : AppTheme.text.secondary
                }
            }
            Label {
                text: applicationWindow.connectedCount + "/" + applicationWindow.connectionList.length + qsTr(" Quellen")
                font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.secondary
            }
            Label {
                text: Math.round(applicationWindow.diagnostics.rate || 0).toLocaleString(Qt.locale("de_DE"), "f", 0) + qsTr(" Werte/s")
                font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.secondary
            }
            Row {
                spacing: 8
                Accessible.role: Accessible.ProgressBar
                Accessible.name: qsTr("Rohpuffer %1 Prozent belegt").arg(Math.round(applicationWindow.bufferFill * 100))
                Label { text: qsTr("Rohpuffer"); font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.secondary; anchors.verticalCenter: parent.verticalCenter }
                Rectangle {
                    width: 80; height: 6; radius: 3; color: AppTheme.borders.primary
                    anchors.verticalCenter: parent.verticalCenter
                    Rectangle { width: parent.width * applicationWindow.bufferFill; height: parent.height; radius: 3; color: applicationWindow.bufferFill > 0.8 ? AppTheme.palette.warning : AppTheme.palette.primary }
                }
                Label {
                    text: Math.round(applicationWindow.bufferFill * 100) + " %"
                    font.family: AppTheme.monoFamily; font.pixelSize: AppTheme.fontSize.small
                    color: applicationWindow.bufferFill > 0.8 ? "#F5CF83" : AppTheme.text.secondary
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            UiButton {
                id: lossBadge
                readonly property int invalid: applicationWindow.diagnostics.invalid || 0
                readonly property int evicted: applicationWindow.diagnostics.evicted || 0
                readonly property var tone: applicationWindow.losses ? AppTheme.tone.danger : (evicted || invalid) ? AppTheme.tone.warning : AppTheme.tone.live
                implicitHeight: 20
                font.pixelSize: AppTheme.fontSize.small
                font.weight: Font.Normal
                iconName: applicationWindow.losses || evicted || invalid ? "warning" : "check"
                text: applicationWindow.losses ? qsTr("%1 verworfen").arg(applicationWindow.losses.toLocaleString(Qt.locale("de_DE"), "f", 0))
                    : evicted ? qsTr("%1 ersetzt").arg(evicted.toLocaleString(Qt.locale("de_DE"), "f", 0))
                    : invalid ? qsTr("%1 ungültig").arg(invalid)
                    : qsTr("Keine Verluste")
                toneBackground: tone.bg; toneBorder: tone.border; toneText: tone.text
                background: Rectangle { radius: 10; color: lossBadge.tone.bg; border.color: lossBadge.visualFocus ? AppTheme.borders.focus : lossBadge.tone.border }
                onClicked: diagnosticsPopup.open()
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignRight
                text: applicationWindow.statusText
                elide: Text.ElideRight
                font.pixelSize: AppTheme.fontSize.small
                color: applicationWindow.statusLevel === "error" ? "#F29C99" : applicationWindow.statusLevel === "warning" ? AppTheme.palette.warning : AppTheme.text.hint
                ToolTip.visible: statusHover.hovered && truncated
                ToolTip.text: applicationWindow.statusText
                HoverHandler { id: statusHover }
            }
            Label {
                text: applicationWindow.displayPaused ? qsTr("Anzeige pausiert") : qsTr("Anzeige live · %1 Hz").arg(Math.round(1000 / Math.max(1, applicationWindow.frameIntervalMs)))
                font.pixelSize: AppTheme.fontSize.small
                font.weight: applicationWindow.displayPaused ? Font.Medium : Font.Normal
                color: applicationWindow.displayPaused ? "#F5CF83" : AppTheme.text.secondary
            }
        }

        Popup {
            id: diagnosticsPopup
            x: lossBadge.x
            y: -implicitHeight - 6
            width: 360
            padding: 16
            background: Rectangle { color: AppTheme.surfaces.dialog; border.color: AppTheme.borders.strong; radius: AppTheme.radius.large }
            contentItem: ColumnLayout {
                spacing: 6
                Caption { text: qsTr("Diagnose") }
                Repeater {
                    model: [
                        [qsTr("Empfangen"), applicationWindow.diagnostics.received],
                        [qsTr("Ungültig"), applicationWindow.diagnostics.invalid],
                        [qsTr("Verworfen · Eingang"), applicationWindow.diagnostics.ingressDropped],
                        [qsTr("Verworfen · Anzeige"), applicationWindow.diagnostics.displayDropped],
                        [qsTr("Verworfen · Ereignisse"), applicationWindow.diagnostics.eventDropped],
                        [qsTr("Verworfen · Signallimit"), applicationWindow.diagnostics.signalLimitDropped],
                        [qsTr("Rohpuffer ersetzt"), applicationWindow.diagnostics.evicted],
                        [qsTr("Für Anzeige verdichtet"), applicationWindow.diagnostics.displayReduced]
                    ]
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Label { text: modelData[0]; color: AppTheme.text.secondary; Layout.fillWidth: true }
                        Label { text: (modelData[1] || 0).toLocaleString(Qt.locale("de_DE"), "f", 0); font.family: AppTheme.monoFamily }
                    }
                }
                Label {
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    wrapMode: Text.WordWrap
                    font.pixelSize: AppTheme.fontSize.small
                    color: AppTheme.text.hint
                    text: qsTr("Verworfen: Überlast von Eingang oder Anzeige bzw. Signallimit. Ersetzt: ältere Rohwerte durch die Speichergrenze entfernt – die CSV enthält nur gespeicherte Werte.")
                }
            }
        }
    }

    // Shared drag ghost for assigning signals by drag & drop.
    Rectangle {
        id: dragGhost
        property var sourceArea: null
        property string uniqueId: ""
        property string label: ""
        property color swatch: "transparent"
        readonly property bool dragging: !!sourceArea && sourceArea.drag.active
        parent: Overlay.overlay
        z: 1000
        visible: dragging
        width: ghostRow.implicitWidth + 24
        height: 30
        radius: 15
        color: AppTheme.surfaces.control
        border.color: AppTheme.palette.primary
        Drag.active: dragging
        Drag.keys: ["kymo/signal"]
        Drag.hotSpot.x: 14
        Drag.hotSpot.y: 15
        onDraggingChanged: if (applicationWindow.workspaceController) applicationWindow.workspaceController.draggedSignalId = dragging ? uniqueId : ""
        Row {
            id: ghostRow
            anchors.centerIn: parent
            spacing: 8
            Rectangle { width: 10; height: 10; radius: 2; color: dragGhost.swatch; anchors.verticalCenter: parent.verticalCenter }
            Label { text: dragGhost.label; font.weight: Font.Medium; anchors.verticalCenter: parent.verticalCenter }
        }
    }

    Timer { interval: 1000; running: applicationWindow.uiReady; repeat: true; onTriggered: refreshDiagnostics() }
    WorkspaceDialogs { id: workspaceDialogs; workspaceController: applicationWindow.workspaceController }
    SourcesDialog { id: sourcesDialog; objectName: "sourcesDialog"; parent: Overlay.overlay; anchors.centerIn: parent; backend: Backend }
    ChartCreationDialog {
        id: chartCreation
        objectName: "chartCreationDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        workspaceController: applicationWindow.workspaceController
        onRequested: function(type, title, signalIds) { applicationWindow.createChartWithSignals(type, title, signalIds) }
    }
    PreferencesDialog { id: preferences; parent: Overlay.overlay; anchors.centerIn: parent; backendInterface: Backend; onPreferencesApplied: { rememberPreferences(); workspaceController.trimDisplays() } }
    FileDialog { id: csvDialog; title: qsTr("Rohdaten als CSV speichern"); fileMode: FileDialog.SaveFile; defaultSuffix: "csv"; nameFilters: ["CSV (*.csv)"]; onAccepted: Backend.export_samples(selectedFile.toString(), exportSignalId) }
    FileDialog {
        id: imageDialog; title: qsTr("Als PNG speichern"); fileMode: FileDialog.SaveFile; defaultSuffix: "png"; nameFilters: ["PNG (*.png)"]
        onAccepted: {
            var path = Backend.export_local_path(selectedFile.toString())
            if (!path) return
            var source = exportImageChartId ? workspaceController.windowForChart(exportImageChartId) : chartWorkspace
            var started = source && source.grabToImage(function(result) {
                var saved = result.saveToFile(path)
                showStatusMessage(saved ? "success" : "error", saved ? qsTr("PNG gespeichert.") : qsTr("PNG konnte nicht gespeichert werden."))
            })
            if (!started) showStatusMessage("error", qsTr("Bildaufnahme konnte nicht gestartet werden."))
        }
    }
    FileDialog { id: configExportDialog; title: qsTr("Konfiguration speichern"); fileMode: FileDialog.SaveFile; defaultSuffix: "json"; nameFilters: ["JSON (*.json)"]; onAccepted: Backend.save_configuration_to_file(selectedFile.toString()) }
    FileDialog {
        id: configImportDialog; title: qsTr("Konfiguration laden"); nameFilters: ["JSON (*.json)"]
        onAccepted: {
            if (Backend.load_configuration_from_file(selectedFile.toString())) {
                workspaceController.restoreSnapshot(Backend.get_workspace())
                AppTheme.displayPointLimit = Backend.get_performance_settings().display_points_per_signal
                refreshConnections()
                scheduleLayout()
            }
        }
    }
    ConfirmDialog {
        id: importConfirmation
        title: qsTr("Konfiguration ersetzen?")
        text: qsTr("Ein erfolgreicher Import stoppt Verbindungen und leert Messwerte. Vorher benötigte Rohdaten als CSV exportieren. Konfigurationen können Zugangsdaten enthalten.")
        onAccepted: configImportDialog.open()
    }
    ConfirmDialog {
        id: clearConfirmation
        title: qsTr("Messwerte leeren?")
        text: qsTr("Diagramme und Rohdatenpuffer werden geleert. Quellen und Zuordnungen bleiben bestehen. Dies kann nicht rückgängig gemacht werden.")
        onAccepted: { Backend.clear_measurements(); workspaceController.clearDisplays(); refreshDiagnostics() }
    }
    Shortcut { sequence: "Ctrl+N"; onActivated: chartCreation.open() }
    Shortcut { sequence: "Ctrl+E"; onActivated: { exportSignalId = ""; csvDialog.open() } }
    Shortcut { sequence: "Ctrl+Space"; onActivated: setDisplayPaused(!displayPaused) }
    Shortcut { sequence: "Ctrl+B"; onActivated: sidebarsVisible = !sidebarsVisible }
    Shortcut { sequence: "Ctrl+,"; onActivated: preferences.open() }
    Shortcut { sequence: "Ctrl+S"; onActivated: { if (saveWorkspace()) showStatusMessage("success", qsTr("Layout gespeichert.")) } }
    Shortcut { sequence: "Ctrl+0"; onActivated: workspaceController.fitAll() }
    onClosing: function(close) {
        if (!Backend.shutdown()) { close.accepted = false; return }
        saveWorkspace()
        if (visibility !== Window.Maximized && visibility !== Window.FullScreen) {
            uiState.windowWidth = width; uiState.windowHeight = height
        }
        uiState.sidebarsVisible = sidebarsVisible
        if (sidebarsVisible) { uiState.sourcesWidth = sourcesPanel.width; uiState.inspectorWidth = inspector.width }
    }
}

/**
 * FloatingChartWindow.qml
 *
 * Chart tile of the workspace. Hosts one renderer; position and size come from
 * the workspace layout ("tile", "focus") or from the user ("free").
 */

import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Common 1.0
import Theme 1.0
import "../Workbench"

Rectangle {
    id: floatingWindow
    objectName: "floatingChartWindow_" + chartId

    property string chartId: ""
    property string chartTitle: "Chart"
    property string chartType: "xy_line"
    // The workspace owns chart state, assignments and data routing.
    property var workspaceController: null
    property string connectionId: ""
    property bool autoDeleteConnectionOnClose: false
    property bool isDocked: false
    property string dockPosition: ""

    property alias chartRenderer: chartLoader.item

    property bool isMinimized: false
    property bool isMaximized: false
    property int zOrder: 0
    property rect restoreGeometry: Qt.rect(100, 100, 800, 600)
    property rect minimizeRestoreGeometry: Qt.rect(0, 0, 0, 0)

    property bool isDragging: false
    property bool isResizing: false
    property point dragStartPos: Qt.point(0, 0)
    property point windowStartPos: Qt.point(0, 0)
    property color dragBorderColor: AppTheme.palette.primary
    property real dragShadowIntensity: 1.0
    property bool showDockingPreview: false
    property string previewDockPosition: ""
    property int dragUpdateThrottle: 8
    property var lastDragUpdate: Date.now()

    readonly property bool freeLayout: !workspaceController || workspaceController.layoutMode === "free"
    readonly property bool isActive: !!workspaceController && workspaceController.activeChartId === chartId
    readonly property bool signalDragActive: !!workspaceController && workspaceController.draggedSignalId !== ""
    readonly property var badgeColors: AppTheme.chartTypeBadgeColors(chartType)

    color: AppTheme.surfaces.panel
    border.color: isDragging ? dragBorderColor : isActive ? AppTheme.palette.primary : AppTheme.borders.primary
    border.width: 1
    radius: AppTheme.radius.large
    clip: true
    width: 800
    height: 600

    states: [
        State {
            name: "maximized"
            when: floatingWindow.isMaximized
            AnchorChanges {
                target: floatingWindow
                anchors.left: floatingWindow.parent.left
                anchors.right: floatingWindow.parent.right
                anchors.top: floatingWindow.parent.top
                anchors.bottom: floatingWindow.parent.bottom
            }
        },
        State {
            name: "dockedLeft"
            when: floatingWindow.isDocked && floatingWindow.dockPosition === "left"
            AnchorChanges { target: floatingWindow; anchors.left: floatingWindow.parent.left; anchors.top: floatingWindow.parent.top; anchors.bottom: floatingWindow.parent.bottom }
            PropertyChanges { target: floatingWindow; width: floatingWindow.parent.width / 2 }
        },
        State {
            name: "dockedRight"
            when: floatingWindow.isDocked && floatingWindow.dockPosition === "right"
            AnchorChanges { target: floatingWindow; anchors.right: floatingWindow.parent.right; anchors.top: floatingWindow.parent.top; anchors.bottom: floatingWindow.parent.bottom }
            PropertyChanges { target: floatingWindow; width: floatingWindow.parent.width / 2 }
        },
        State {
            name: "dockedTop"
            when: floatingWindow.isDocked && floatingWindow.dockPosition === "top"
            AnchorChanges { target: floatingWindow; anchors.left: floatingWindow.parent.left; anchors.right: floatingWindow.parent.right; anchors.top: floatingWindow.parent.top }
            PropertyChanges { target: floatingWindow; height: floatingWindow.parent.height / 2 }
        },
        State {
            name: "dockedBottom"
            when: floatingWindow.isDocked && floatingWindow.dockPosition === "bottom"
            AnchorChanges { target: floatingWindow; anchors.left: floatingWindow.parent.left; anchors.right: floatingWindow.parent.right; anchors.bottom: floatingWindow.parent.bottom }
            PropertyChanges { target: floatingWindow; height: floatingWindow.parent.height / 2 }
        }
    ]

    z: zOrder

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 1
        spacing: 0

        Rectangle {
            id: titleBar
            Layout.fillWidth: true
            Layout.preferredHeight: AppTheme.heights.chartHeader
            color: "transparent"

            Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: AppTheme.borders.primary; visible: !floatingWindow.isMinimized }

            MouseArea {
                id: dragArea
                anchors.fill: parent
                cursorShape: floatingWindow.freeLayout && !floatingWindow.isDocked && !floatingWindow.isMaximized ? Qt.SizeAllCursor : Qt.ArrowCursor
                property point pressPosInParent: Qt.point(0, 0)

                onPressed: (mouse) => {
                    if (floatingWindow.workspaceController) floatingWindow.workspaceController.bringToFront(floatingWindow.chartId)
                    if (!floatingWindow.freeLayout || floatingWindow.isDocked || floatingWindow.isMaximized) return
                    floatingWindow.dragStartPos = Qt.point(mouse.x, mouse.y)
                    floatingWindow.windowStartPos = Qt.point(floatingWindow.x, floatingWindow.y)
                    pressPosInParent = dragArea.mapToItem(floatingWindow.parent, mouse.x, mouse.y)
                    floatingWindow.isDragging = true
                }
                onPositionChanged: (mouse) => {
                    if (!floatingWindow.isDragging || floatingWindow.isDocked) return
                    var now = Date.now()
                    if (now - floatingWindow.lastDragUpdate < floatingWindow.dragUpdateThrottle) return
                    floatingWindow.lastDragUpdate = now
                    var current = dragArea.mapToItem(floatingWindow.parent, mouse.x, mouse.y)
                    var nextX = floatingWindow.windowStartPos.x + current.x - pressPosInParent.x
                    var nextY = floatingWindow.windowStartPos.y + current.y - pressPosInParent.y
                    if (floatingWindow.parent) {
                        nextX = Math.max(0, Math.min(Math.max(0, floatingWindow.parent.width - floatingWindow.width), nextX))
                        nextY = Math.max(0, Math.min(Math.max(0, floatingWindow.parent.height - floatingWindow.height), nextY))
                    }
                    floatingWindow.x = nextX
                    floatingWindow.y = nextY
                    checkDockingZonesPreview()
                }
                onReleased: {
                    if (!floatingWindow.isDragging) return
                    floatingWindow.isDragging = false
                    floatingWindow.showDockingPreview = false
                    checkDockingZones()
                    if (floatingWindow.workspaceController)
                        floatingWindow.workspaceController.updateChartGeometry(floatingWindow.chartId, floatingWindow.x, floatingWindow.y, floatingWindow.width, floatingWindow.height)
                }
                onDoubleClicked: {
                    if (floatingWindow.freeLayout) toggleMaximize()
                    else if (floatingWindow.workspaceController)
                        floatingWindow.workspaceController.layoutMode = floatingWindow.workspaceController.layoutMode === "focus" ? "tile" : "focus"
                }
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 6
                spacing: 10

                Label {
                    text: AppTheme.chartTypeBadge(floatingWindow.chartType)
                    font.family: AppTheme.monoFamily
                    font.pixelSize: AppTheme.fontSize.caption
                    color: floatingWindow.badgeColors[1]
                    leftPadding: 6; rightPadding: 6; topPadding: 2; bottomPadding: 2
                    background: Rectangle { radius: AppTheme.radius.small; color: floatingWindow.badgeColors[0] }
                    Accessible.name: AppTheme.chartTypeName(floatingWindow.chartType)
                    ToolTip.visible: badgeHover.hovered
                    ToolTip.text: AppTheme.chartTypeName(floatingWindow.chartType)
                    HoverHandler { id: badgeHover }
                }
                Label {
                    text: floatingWindow.chartTitle
                    font.weight: Font.DemiBold
                    color: AppTheme.text.primary
                    elide: Text.ElideRight
                    Layout.maximumWidth: Math.max(80, floatingWindow.width * 0.3)
                }

                // Legend: every curve of this chart; click toggles visibility.
                Flickable {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    contentWidth: legendRow.width
                    clip: true
                    interactive: contentWidth > width
                    opacity: AppTheme.showLegend ? 1 : 0
                    enabled: AppTheme.showLegend
                    Row {
                        id: legendRow
                        spacing: 6
                        Repeater {
                            model: floatingWindow.workspaceController ? floatingWindow.workspaceController.chartLineModel : null
                            delegate: AbstractButton {
                                id: chip
                                // The "visible" role would shadow Item.visible; read roles via model.
                                required property var model
                                readonly property string lineKey: model.lineKey
                                readonly property string displayName: model.displayName
                                readonly property color lineColor: model.color
                                readonly property bool mine: model.chartId === floatingWindow.chartId
                                readonly property bool shown: model.visible
                                width: mine ? implicitWidth : 0
                                height: 22
                                implicitWidth: chipRow.implicitWidth + 16
                                opacity: mine ? 1 : 0
                                enabled: mine
                                hoverEnabled: true
                                Accessible.name: displayName + (shown ? qsTr(" ausblenden") : qsTr(" einblenden"))
                                ToolTip.visible: hovered
                                ToolTip.delay: 600
                                ToolTip.text: shown ? qsTr("Klicken zum Ausblenden") : qsTr("Klicken zum Einblenden")
                                onClicked: floatingWindow.workspaceController.setLineVisibility(lineKey, !shown)
                                contentItem: Item {
                                    Row {
                                        id: chipRow
                                        anchors.centerIn: parent
                                        spacing: 6
                                        Rectangle { width: 10; height: 10; radius: 2; anchors.verticalCenter: parent.verticalCenter; color: chip.shown ? chip.lineColor : "transparent"; border.color: chip.lineColor }
                                        Text {
                                            text: chip.displayName
                                            font.family: AppTheme.fontFamily
                                            font.pixelSize: AppTheme.fontSize.small
                                            font.strikeout: !chip.shown
                                            color: chip.shown ? AppTheme.text.label : AppTheme.text.hint
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                    }
                                }
                                background: Rectangle {
                                    radius: 11
                                    color: chip.shown ? AppTheme.surfaces.control : "transparent"
                                    border.color: chip.visualFocus ? AppTheme.borders.focus : AppTheme.borders.primary
                                }
                            }
                        }
                    }
                }

                Label {
                    readonly property var renderer: floatingWindow.chartRenderer
                    visible: floatingWindow.chartType === "time_series" && !!renderer && renderer.timeWindow !== undefined
                    text: renderer && renderer.autoScroll ? Math.round(renderer.timeWindow) + qsTr(" s · folgt") : qsTr("Zeit fest")
                    font.pixelSize: AppTheme.fontSize.small
                    color: AppTheme.text.secondary
                    leftPadding: 8; rightPadding: 8; topPadding: 2; bottomPadding: 2
                    background: Rectangle { radius: 11; color: AppTheme.surfaces.control; border.color: AppTheme.borders.primary }
                }
                Label {
                    readonly property var renderer: floatingWindow.chartRenderer
                    visible: !!renderer && renderer.autoScaleY === false
                    text: qsTr("Y manuell")
                    font.pixelSize: AppTheme.fontSize.small
                    color: AppTheme.palette.warning
                    leftPadding: 8; rightPadding: 8; topPadding: 2; bottomPadding: 2
                    background: Rectangle { radius: 11; color: "transparent"; border.color: "#4A3B1C" }
                }
                IconButton {
                    iconName: "fit"
                    tip: qsTr("Daten einpassen")
                    visible: floatingWindow.chartType !== "xyz_scatter"
                    onClicked: if (floatingWindow.chartRenderer && floatingWindow.chartRenderer.fitToData) floatingWindow.chartRenderer.fitToData()
                }
                IconButton {
                    iconName: "more"
                    tip: qsTr("Weitere Aktionen")
                    onClicked: chartMenu.popup()
                    Menu {
                        id: chartMenu
                        MenuItem {
                            text: floatingWindow.workspaceController && floatingWindow.workspaceController.layoutMode === "focus" && floatingWindow.isActive ? qsTr("Zurück zu Kacheln") : qsTr("Fokussieren")
                            onTriggered: {
                                var wc = floatingWindow.workspaceController
                                var leaveFocus = wc.layoutMode === "focus" && floatingWindow.isActive
                                wc.bringToFront(floatingWindow.chartId)
                                wc.layoutMode = leaveFocus ? "tile" : "focus"
                            }
                        }
                        MenuItem {
                            text: floatingWindow.isMinimized ? qsTr("Wiederherstellen") : qsTr("Minimieren")
                            enabled: floatingWindow.freeLayout
                            onTriggered: toggleMinimize()
                        }
                        MenuSeparator {}
                        MenuItem { text: qsTr("Diagramm schließen"); onTriggered: closeWindow() }
                    }
                }
            }
        }

        Item {
            id: chartContent
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !floatingWindow.isMinimized

            Loader {
                id: chartLoader
                anchors.fill: parent
                anchors.margins: 8
                source: getChartRendererQml(floatingWindow.chartType)
                asynchronous: true
                onLoaded: {
                    if (item) {
                        item.chartId = floatingWindow.chartId
                        item.chartTitle = floatingWindow.chartTitle
                        if (item.chartType !== undefined) item.chartType = floatingWindow.chartType
                    }
                    syncRendererState()
                    if (floatingWindow.workspaceController) floatingWindow.workspaceController.rendererReady(floatingWindow.chartId)
                }
                onStatusChanged: if (status === Loader.Error) console.error("FloatingChartWindow: Failed to load chart renderer:", source)
            }

            BusyIndicator { anchors.centerIn: parent; running: chartLoader.status === Loader.Loading; visible: running }

            Label {
                anchors.centerIn: parent
                width: parent.width - 48
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                visible: chartLoader.status === Loader.Ready && !!floatingWindow.workspaceController
                    && floatingWindow.workspaceController.assignmentRevision >= 0 && !floatingWindow.hasLines()
                text: qsTr("Noch keine Kurve. Ein Signal aus der Liste links hierher ziehen.")
                color: AppTheme.text.hint
            }

            // Selecting a chart must not swallow zoom/pan gestures of the renderer.
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.AllButtons
                onPressed: (mouse) => {
                    if (floatingWindow.workspaceController) floatingWindow.workspaceController.bringToFront(floatingWindow.chartId)
                    mouse.accepted = false
                }
            }

            // Drop zones shown while a signal is dragged from the source list.
            Rectangle {
                anchors.fill: parent
                visible: floatingWindow.signalDragActive
                color: Qt.rgba(11 / 255, 15 / 255, 20 / 255, 0.92)
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12
                    Repeater {
                        model: floatingWindow.chartType === "time_series"
                            ? [{ field: "y", title: "Y(t)", text: qsTr("Messwert über Zeit") },
                               { field: "x", title: "X(t)", text: qsTr("X-Wert über Zeit · nur mit explizitem X im Datenpaket") }]
                            : [{ field: "", title: AppTheme.chartTypeBadge(floatingWindow.chartType), text: floatingWindow.chartType === "xyz_scatter" ? qsTr("Benötigt X, Y und Z im Datenpaket") : qsTr("Benötigt X und Y im Datenpaket") }]
                        delegate: DropArea {
                            id: zone
                            required property var modelData
                            readonly property bool assigned: !!floatingWindow.workspaceController && floatingWindow.workspaceController.assignmentRevision >= 0
                                && floatingWindow.workspaceController.chartLineModel.hasLineForChart(floatingWindow.workspaceController.draggedSignalId, floatingWindow.chartId, modelData.field || null)
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            keys: ["kymo/signal"]
                            function acceptSignal(uniqueId) {
                                if (!assigned) floatingWindow.workspaceController.assignSignal(uniqueId, floatingWindow.chartId, modelData.field || null)
                            }
                            Rectangle {
                                anchors.fill: parent
                                radius: AppTheme.radius.large
                                color: zone.containsDrag && !zone.assigned ? Qt.rgba(77 / 255, 182 / 255, 240 / 255, 0.14) : "transparent"
                                border.width: 2
                                border.color: zone.containsDrag && !zone.assigned ? AppTheme.palette.primary : AppTheme.borders.strong
                                ColumnLayout {
                                    anchors.centerIn: parent
                                    width: parent.width - 24
                                    spacing: 4
                                    Label { text: zone.modelData.title; font.family: AppTheme.monoFamily; font.pixelSize: 18; color: zone.assigned ? AppTheme.text.hint : "#8FD0F6"; Layout.alignment: Qt.AlignHCenter }
                                    Label { text: zone.assigned ? qsTr("Bereits zugeordnet") : qsTr("Loslassen zum Zuordnen"); font.weight: Font.DemiBold; color: zone.assigned ? AppTheme.text.hint : AppTheme.text.primary; Layout.alignment: Qt.AlignHCenter }
                                    Label { text: zone.modelData.text; font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.secondary; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    function hasLines() {
        var lines = workspaceController ? workspaceController.chartLineModel : null
        if (!lines) return false
        for (var i = 0; i < lines.count; i++) if (lines.get(i).chartId === chartId) return true
        return false
    }

    // Resize handles (bottom-right corner)
    Rectangle {
        id: resizeHandle
        width: 16
        height: 16
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 4
        color: AppTheme.surfaces.muted
        radius: 2
        visible: floatingWindow.freeLayout && !floatingWindow.isMinimized && !floatingWindow.isMaximized && !floatingWindow.isDocked

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.SizeFDiagCursor

            property point clickPos: Qt.point(0, 0)
            property point pressPosInParent: Qt.point(0, 0)
            property size startSize: Qt.size(0, 0)

            onPressed: (mouse) => {
                clickPos = Qt.point(mouse.x, mouse.y)
                startSize = Qt.size(floatingWindow.width, floatingWindow.height)
                pressPosInParent = resizeHandle.mapToItem(floatingWindow.parent, mouse.x, mouse.y)
                floatingWindow.isResizing = true
            }

            onPositionChanged: (mouse) => {
                var currentPosInParent = resizeHandle.mapToItem(floatingWindow.parent, mouse.x, mouse.y)
                var delta = Qt.point(currentPosInParent.x - pressPosInParent.x,
                                     currentPosInParent.y - pressPosInParent.y)
                var maxW = floatingWindow.parent ? floatingWindow.parent.width : 1000000
                var maxH = floatingWindow.parent ? floatingWindow.parent.height : 1000000
                var minW = Math.min(400, maxW)
                var minH = Math.min(300, maxH)

                floatingWindow.width = Math.max(minW, Math.min(maxW, startSize.width + delta.x))
                floatingWindow.height = Math.max(minH, Math.min(maxH, startSize.height + delta.y))
                clampToParent()
            }

            onReleased: {
                floatingWindow.isResizing = false

                if (floatingWindow.workspaceController) {
                    floatingWindow.workspaceController.updateChartGeometry(
                        floatingWindow.chartId,
                        floatingWindow.x,
                        floatingWindow.y,
                        floatingWindow.width,
                        floatingWindow.height
                    )
                }
            }
        }
    }

    // Docking Zone Preview Overlay
    Rectangle {
        id: dockPreviewOverlay
        color: Qt.rgba(63 / 255, 183 / 255, 255 / 255, 0.25)
        border.color: AppTheme.palette.primary
        border.width: 3
        radius: 4
        visible: floatingWindow.showDockingPreview
        z: -1  // Behind window

        x: {
            if (!parent) return 0
            if (floatingWindow.previewDockPosition === "left") return 0
            if (floatingWindow.previewDockPosition === "right") return parent.width / 2
            return 0
        }

        y: {
            if (!parent) return 0
            if (floatingWindow.previewDockPosition === "top") return 0
            if (floatingWindow.previewDockPosition === "bottom") return parent.height / 2
            return 0
        }

        width: {
            if (!parent) return 0
            if (floatingWindow.previewDockPosition === "left" || floatingWindow.previewDockPosition === "right")
                return parent.width / 2
            return parent.width
        }

        height: {
            if (!parent) return 0
            if (floatingWindow.previewDockPosition === "top" || floatingWindow.previewDockPosition === "bottom")
                return parent.height / 2
            return parent.height
        }

        Behavior on x {
            enabled: !floatingWindow.isDragging
            NumberAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }
        Behavior on y {
            enabled: !floatingWindow.isDragging
            NumberAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }
        Behavior on width {
            enabled: !floatingWindow.isDragging
            NumberAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }
        Behavior on height {
            enabled: !floatingWindow.isDragging
            NumberAnimation { duration: 150; easing.type: Easing.InOutQuad }
        }

        Text {
            anchors.centerIn: parent
            text: {
                switch(floatingWindow.previewDockPosition) {
                    case "left": return "◀"
                    case "right": return "▶"
                    case "top": return "▲"
                    case "bottom": return "▼"
                    default: return "⊞"
                }
            }
            font.pixelSize: 48
            color: AppTheme.palette.primary
            opacity: 0.6
        }
    }

    // Narrow renderer port used by WorkspaceController.
    function createSeries(uniqueId, displayName, color, interfaceType, dataId, valueField) {
        if (!chartRenderer || !chartRenderer.createLine) return null
        if (chartRenderer.getLine) {
            var existing = chartRenderer.getLine(uniqueId, valueField)
            if (existing) return existing.series || existing
        }
        return chartRenderer.createLine(uniqueId, displayName, color, interfaceType, dataId, valueField)
    }

    function removeSeries(uniqueId, valueField) {
        if (!chartRenderer || !chartRenderer.removeLine) return false
        return chartRenderer.removeLine(uniqueId, valueField)
    }

    function updateSeries(uniqueId, valueField, displayName, color, visible) {
        if (!chartRenderer || !chartRenderer.updateLineProperties) return false
        chartRenderer.updateLineProperties(uniqueId, valueField, displayName, color, visible)
        return true
    }

    function appendPointsBatch(uniqueId, points) {
        if (!chartRenderer || !chartRenderer.appendPointsBatch) return false
        chartRenderer.appendPointsBatch(uniqueId, points)
        return true
    }

    function appendPointsBatch3D(uniqueId, points) {
        if (!chartRenderer || !chartRenderer.appendPointsBatch3D) return false
        chartRenderer.appendPointsBatch3D(uniqueId, points)
        return true
    }

    function clampToParent() {
        if (!parent) return
        if (floatingWindow.isDocked || floatingWindow.isMaximized) return

        if (floatingWindow.width > parent.width) {
            floatingWindow.width = parent.width
        }
        if (floatingWindow.height > parent.height) {
            floatingWindow.height = parent.height
        }

        var maxX = Math.max(0, parent.width - floatingWindow.width)
        var maxY = Math.max(0, parent.height - floatingWindow.height)
        floatingWindow.x = Math.max(0, Math.min(maxX, floatingWindow.x))
        floatingWindow.y = Math.max(0, Math.min(maxY, floatingWindow.y))
    }

    Connections {
        target: floatingWindow.parent
        function onWidthChanged() { clampToParent() }
        function onHeightChanged() { clampToParent() }
    }

    Component.onCompleted: {
        if (floatingWindow.workspaceController) {
            floatingWindow.workspaceController.registerWindow(floatingWindow.chartId, floatingWindow)
        }
        clampToParent()
        syncRendererState()
    }

    onIsDraggingChanged: syncRendererState()
    onIsResizingChanged: syncRendererState()
    onIsMinimizedChanged: syncRendererState()

    function getChartRendererQml(type) {
        switch(type) {
            case "xy_line":
            case "xy_scatter":
                return "../ChartTypes/XYChartView.qml"
            case "time_series":
                return "../ChartTypes/TimeSeriesRenderer.qml"
            case "xyz_surface":
            case "xyz_scatter":
                return "../ChartTypes/XYZChartRenderer.qml"
            default:
                return ""
        }
    }

    function toggleMinimize() {
        if (!floatingWindow.isMinimized) {
            if (floatingWindow.isDocked) {
                undock()
            }
            if (floatingWindow.isMaximized) {
                floatingWindow.isMaximized = false
                floatingWindow.x = floatingWindow.restoreGeometry.x
                floatingWindow.y = floatingWindow.restoreGeometry.y
                floatingWindow.width = floatingWindow.restoreGeometry.width
                floatingWindow.height = floatingWindow.restoreGeometry.height
            }
            floatingWindow.minimizeRestoreGeometry = Qt.rect(floatingWindow.x, floatingWindow.y, floatingWindow.width, floatingWindow.height)
            floatingWindow.isMinimized = true
            floatingWindow.height = titleBar.height
        } else {
            floatingWindow.isMinimized = false
            var restore = floatingWindow.minimizeRestoreGeometry
            if (restore.width <= 0 || restore.height <= 0) {
                restore = Qt.rect(floatingWindow.x, floatingWindow.y, 800, 600)
            }
            floatingWindow.x = restore.x
            floatingWindow.y = restore.y
            floatingWindow.width = restore.width
            floatingWindow.height = restore.height
            clampToParent()
        }
        syncRendererState()
        persistWindowState()
    }

    function toggleMaximize() {
        if (floatingWindow.isDocked) {
            undock()
        }
        if (floatingWindow.isMinimized) {
            toggleMinimize()
        }

        if (!floatingWindow.isMaximized) {
            floatingWindow.restoreGeometry = Qt.rect(floatingWindow.x, floatingWindow.y, floatingWindow.width, floatingWindow.height)
            floatingWindow.isMaximized = true
        } else {
            floatingWindow.isMaximized = false
            floatingWindow.x = floatingWindow.restoreGeometry.x
            floatingWindow.y = floatingWindow.restoreGeometry.y
            floatingWindow.width = floatingWindow.restoreGeometry.width
            floatingWindow.height = floatingWindow.restoreGeometry.height
            clampToParent()
        }
        persistWindowState()
    }

    function closeWindow() {
        if (floatingWindow.workspaceController) {
            floatingWindow.workspaceController.removeChart(floatingWindow.chartId)
        }
    }

    function syncRendererState() {
        if (chartRenderer && chartRenderer.updatesSuspended !== undefined) {
            chartRenderer.updatesSuspended = floatingWindow.isDragging || floatingWindow.isResizing || floatingWindow.isMinimized
        }
    }

    function persistWindowState() {
        if (!floatingWindow.workspaceController) return
        floatingWindow.workspaceController.updateChartWindowState(
            floatingWindow.chartId,
            floatingWindow.isMinimized,
            floatingWindow.isMaximized,
            floatingWindow.restoreGeometry
        )
    }

    function checkDockingZonesPreview() {
        if (!parent) return

        var dockThreshold = 80
        var parentWidth = parent.width
        var parentHeight = parent.height

        var leftDist = floatingWindow.x
        var rightDist = parentWidth - (floatingWindow.x + floatingWindow.width)
        var topDist = floatingWindow.y
        var bottomDist = parentHeight - (floatingWindow.y + floatingWindow.height)

        var minDist = Math.min(leftDist, rightDist, topDist, bottomDist)

        if (minDist > dockThreshold) {
            floatingWindow.showDockingPreview = false
            floatingWindow.previewDockPosition = ""
            floatingWindow.dragBorderColor = AppTheme.palette.primary
            return
        }

        floatingWindow.showDockingPreview = true
        floatingWindow.dragBorderColor = AppTheme.palette.success

        if (minDist === leftDist) {
            floatingWindow.previewDockPosition = "left"
        } else if (minDist === rightDist) {
            floatingWindow.previewDockPosition = "right"
        } else if (minDist === topDist) {
            floatingWindow.previewDockPosition = "top"
        } else if (minDist === bottomDist) {
            floatingWindow.previewDockPosition = "bottom"
        }
    }

    function checkDockingZones() {
        if (!parent) return

        var dockThreshold = 50
        var parentWidth = parent.width
        var parentHeight = parent.height

        // Check left edge
        if (floatingWindow.x < dockThreshold) {
            dockToEdge("left")
        }
        // Check right edge
        else if (floatingWindow.x + floatingWindow.width > parentWidth - dockThreshold) {
            dockToEdge("right")
        }
        // Check top edge
        else if (floatingWindow.y < dockThreshold) {
            dockToEdge("top")
        }
        // Check bottom edge
        else if (floatingWindow.y + floatingWindow.height > parentHeight - dockThreshold) {
            dockToEdge("bottom")
        }
    }

    function dockToEdge(edge) {
        if (!parent) return

        if (!floatingWindow.isDocked) {
            floatingWindow.restoreGeometry = Qt.rect(floatingWindow.x, floatingWindow.y, floatingWindow.width, floatingWindow.height)
        }

        floatingWindow.isDocked = true
        floatingWindow.dockPosition = edge
        floatingWindow.isMaximized = false

        if (floatingWindow.workspaceController) {
            floatingWindow.workspaceController.updateChartDocking(floatingWindow.chartId, true, edge)
            persistWindowState()
        }
    }

    function undock() {
        floatingWindow.isDocked = false
        floatingWindow.dockPosition = ""
        floatingWindow.x = floatingWindow.restoreGeometry.x
        floatingWindow.y = floatingWindow.restoreGeometry.y
        floatingWindow.width = floatingWindow.restoreGeometry.width
        floatingWindow.height = floatingWindow.restoreGeometry.height
        clampToParent()

        if (floatingWindow.workspaceController) {
            floatingWindow.workspaceController.updateChartDocking(floatingWindow.chartId, false, "")
            floatingWindow.workspaceController.updateChartGeometry(
                floatingWindow.chartId,
                floatingWindow.x,
                floatingWindow.y,
                floatingWindow.width,
                floatingWindow.height
            )
        }
    }

    Component.onDestruction: {
        if (floatingWindow.workspaceController) {
            floatingWindow.workspaceController.unregisterWindow(floatingWindow.chartId, floatingWindow)
        }
    }
}

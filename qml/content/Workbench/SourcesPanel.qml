// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/**
 * Left column: data sources with their signals. Connection state is read from
 * the backend; signal and assignment state from the workspace controller.
 */
Rectangle {
    id: root
    property var workspaceController
    property var backend
    property Item dragGhost
    property string selectedSignalId: ""
    property var latestValues: ({})
    property var errors: ({})
    property var collapsed: ({})
    signal signalSelected(string uniqueId)
    signal sourceRequested(string connectionId)
    signal addSourceRequested()
    signal addSignalRequested()

    color: AppTheme.surfaces.panel

    function refreshConnections() {
        if (!backend || !backend.get_connections) return
        var list = backend.get_connections()
        connections.clear()
        for (var i = 0; i < list.length; i++)
            connections.append({ connectionId: list[i].id, name: list[i].name, type: list[i].type, status: list[i].status })
    }
    function statusColor(status) {
        return status === "connected" ? AppTheme.palette.success : status === "connecting" ? AppTheme.palette.warning
            : status === "error" ? AppTheme.palette.danger : AppTheme.palette.idle
    }
    function statusText(status, connectionId) {
        if (status === "connected") return qsTr("verbunden")
        if (status === "connecting") return qsTr("verbindet …")
        if (status === "error") return qsTr("Fehler: ") + (errors[connectionId] || qsTr("unbekannt"))
        return qsTr("getrennt")
    }
    function belongsTo(uniqueId, connectionId) { return String(uniqueId).indexOf(connectionId + "_") === 0 }
    function hasConnection(uniqueId) {
        for (var i = 0; i < connections.count; i++) if (belongsTo(uniqueId, connections.get(i).connectionId)) return true
        return false
    }
    function matches(name, uniqueId, type) {
        var q = search.text.trim().toLowerCase()
        return !q || (name + " " + uniqueId + " " + type).toLowerCase().indexOf(q) !== -1
    }
    function usageText(uniqueId) {
        var n = 0
        var lines = workspaceController.chartLineModel
        for (var i = 0; i < lines.count; i++) if (lines.get(i).uniqueId === uniqueId) n++
        return n === 0 ? qsTr("nicht zugeordnet") : n === 1 ? qsTr("1 Diagramm") : n + qsTr(" Diagramme")
    }
    function formatValue(value) {
        if (value === undefined || value === null || !isFinite(value)) return "–"
        return Number(value).toPrecision(5).replace("-", "−")
    }
    function pollValues() {
        if (!backend || !backend.get_signal_statistics || !workspaceController) return
        var next = ({})
        var signalModel = workspaceController.signalModel
        for (var i = 0; i < signalModel.count; i++) {
            var id = signalModel.get(i).uniqueId
            next[id] = backend.get_signal_statistics(id).latest
        }
        latestValues = next
    }
    function setCollapsed(connectionId, value) {
        var next = Object.assign({}, collapsed)
        next[connectionId] = value
        collapsed = next
    }

    ListModel { id: connections }
    Component.onCompleted: refreshConnections()
    Timer { interval: 1000; running: root.visible; repeat: true; triggeredOnStart: true; onTriggered: root.pollValues() }
    Connections {
        target: root.backend
        ignoreUnknownSignals: true
        function onConnections_changed() { root.refreshConnections() }
        function onConnection_status_changed(connectionId, status, details) {
            if (details && details.error) {
                var next = Object.assign({}, root.errors)
                next[connectionId] = details.error
                root.errors = next
            }
            for (var i = 0; i < connections.count; i++)
                if (connections.get(i).connectionId === connectionId) connections.setProperty(i, "status", status)
        }
    }

    Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: AppTheme.borders.primary }

    component SignalRow: ItemDelegate {
        id: row
        property string uniqueId
        property string name
        property color swatch
        property bool dimmed: false
        height: 40
        leftPadding: 30
        rightPadding: 10
        highlighted: root.selectedSignalId === uniqueId
        Accessible.name: name
        onClicked: root.signalSelected(uniqueId)
        background: Rectangle {
            radius: AppTheme.radius.medium
            color: row.highlighted ? AppTheme.palette.primarySoft : row.hovered ? AppTheme.surfaces.hover : "transparent"
            border.color: row.visualFocus ? AppTheme.borders.focus : row.highlighted ? AppTheme.palette.primaryBorder : "transparent"
        }
        contentItem: RowLayout {
            spacing: 10
            Rectangle { width: 10; height: 10; radius: 2; color: row.swatch; opacity: row.dimmed ? 0.5 : 1 }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                Label { text: row.name; elide: Text.ElideRight; Layout.fillWidth: true; color: row.dimmed ? AppTheme.text.hint : AppTheme.text.primary; font.weight: row.highlighted ? Font.Medium : Font.Normal }
                Label {
                    text: root.workspaceController.assignmentRevision >= 0 ? root.usageText(row.uniqueId) : ""
                    font.pixelSize: AppTheme.fontSize.caption
                    color: AppTheme.text.hint
                }
            }
            Label {
                text: root.formatValue(root.latestValues[row.uniqueId])
                font.family: AppTheme.monoFamily
                font.pixelSize: AppTheme.fontSize.small
                color: row.dimmed ? AppTheme.text.hint : AppTheme.text.primary
                horizontalAlignment: Text.AlignRight
                Layout.preferredWidth: 64
            }
        }
        // Drag onto a chart to assign; the shared ghost carries the drop.
        MouseArea {
            id: dragMouse
            anchors.fill: parent
            drag.target: root.dragGhost
            drag.threshold: 6
            onPressed: (mouse) => {
                var ghost = root.dragGhost
                var p = mapToItem(ghost.parent, mouse.x, mouse.y)
                ghost.x = p.x - 14; ghost.y = p.y - 15
                ghost.uniqueId = row.uniqueId; ghost.label = row.name; ghost.swatch = row.swatch
                ghost.sourceArea = dragMouse
            }
            onReleased: {
                var target = root.dragGhost.Drag.target
                if (drag.active && target && target.acceptSignal) target.acceptSignal(row.uniqueId)
            }
            onClicked: { row.forceActiveFocus(); root.signalSelected(row.uniqueId) }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.rightMargin: 1
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 10
            Layout.topMargin: 10
            Layout.bottomMargin: 6
            Label { text: qsTr("Quellen & Signale"); font.weight: Font.DemiBold; Layout.fillWidth: true }
            IconButton { iconName: "plus"; tip: qsTr("Quelle hinzufügen"); onClicked: root.addSourceRequested() }
        }

        TextField {
            id: search
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 8
            implicitHeight: AppTheme.heights.control
            leftPadding: 32
            placeholderText: qsTr("Signal, Quelle oder ID …")
            Accessible.name: qsTr("Signale durchsuchen")
            selectByMouse: true
            Icon { name: "search"; color: AppTheme.text.hint; x: 10; anchors.verticalCenter: parent.verticalCenter }
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentHeight: groups.implicitHeight
            clip: true
            ScrollBar.vertical: ScrollBar {}

            Column {
                id: groups
                width: parent.width
                leftPadding: 6
                rightPadding: 6

                Repeater {
                    model: connections
                    delegate: Column {
                        id: group
                        required property string connectionId
                        required property string name
                        required property string type
                        required property string status
                        readonly property bool open: !root.collapsed[connectionId]
                        width: groups.width - 12

                        RowLayout {
                            width: parent.width
                            height: 44
                            spacing: 8
                            IconButton {
                                iconName: group.open ? "chevronDown" : "chevronRight"
                                tip: group.open ? qsTr("Einklappen") : qsTr("Ausklappen")
                                implicitWidth: 22
                                onClicked: root.setCollapsed(group.connectionId, group.open)
                            }
                            Rectangle {
                                width: 8; height: 8; radius: 4
                                color: group.status === "connecting" ? "transparent" : root.statusColor(group.status)
                                border.width: group.status === "connecting" ? 2 : 0
                                border.color: root.statusColor(group.status)
                            }
                            ItemDelegate {
                                Layout.fillWidth: true
                                padding: 0
                                background: null
                                Accessible.name: group.name + ", " + root.statusText(group.status, group.connectionId)
                                onClicked: root.sourceRequested(group.connectionId)
                                ToolTip.visible: hovered
                                ToolTip.delay: 600
                                ToolTip.text: qsTr("Einstellungen öffnen")
                                contentItem: ColumnLayout {
                                    spacing: 0
                                    Label { text: group.name; font.weight: Font.Medium; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Label {
                                        text: root.statusText(group.status, group.connectionId)
                                        font.pixelSize: AppTheme.fontSize.small
                                        color: group.status === "error" ? "#F29C99" : group.status === "connecting" ? AppTheme.palette.warning : AppTheme.text.hint
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            IconButton {
                                readonly property bool running: group.status === "connected" || group.status === "connecting"
                                iconName: group.status === "connected" ? "stop" : group.status === "connecting" ? "close" : group.status === "error" ? "refresh" : "play"
                                tip: group.status === "connected" ? qsTr("Stoppen") : group.status === "connecting" ? qsTr("Verbindungsaufbau abbrechen") : group.status === "error" ? qsTr("Erneut verbinden") : qsTr("Starten")
                                onClicked: running ? root.backend.stop_connection(group.connectionId) : root.backend.start_connection(group.connectionId)
                            }
                        }
                        Repeater {
                            model: group.open ? root.workspaceController.signalModel : null
                            delegate: SignalRow {
                                required property var model
                                readonly property bool member: root.belongsTo(model.uniqueId, group.connectionId) && root.matches(model.displayName, model.uniqueId, group.type)
                                width: group.width
                                uniqueId: model.uniqueId
                                name: model.displayName
                                swatch: model.color
                                dimmed: group.status !== "connected"
                                visible: member
                                height: member ? 40 : 0
                            }
                        }
                    }
                }

                // Signals whose source no longer exists (restored or manually added).
                Label {
                    readonly property bool any: {
                        var model = root.workspaceController ? root.workspaceController.signalModel : null
                        if (!model || connections.count < 0) return false
                        for (var i = 0; i < model.count; i++) if (!root.hasConnection(model.get(i).uniqueId)) return true
                        return false
                    }
                    visible: any
                    text: qsTr("Ohne aktive Quelle")
                    leftPadding: 10
                    topPadding: 12
                    bottomPadding: 4
                    font.pixelSize: AppTheme.fontSize.caption
                    font.weight: Font.DemiBold
                    font.capitalization: Font.AllUppercase
                    color: AppTheme.text.hint
                }
                Repeater {
                    model: root.workspaceController ? root.workspaceController.signalModel : null
                    delegate: SignalRow {
                        required property var model
                        readonly property bool member: connections.count >= 0 && !root.hasConnection(model.uniqueId) && root.matches(model.displayName, model.uniqueId, model.interfaceType)
                        width: groups.width - 12
                        uniqueId: model.uniqueId
                        name: model.displayName
                        swatch: model.color
                        dimmed: true
                        visible: member
                        height: member ? 40 : 0
                    }
                }

                Label {
                    visible: connections.count === 0 && (!root.workspaceController || root.workspaceController.signalModel.count === 0)
                    width: groups.width - 12
                    padding: 12
                    wrapMode: Text.WordWrap
                    color: AppTheme.text.secondary
                    text: qsTr("Noch keine Datenquelle. Seriell, TCP, MQTT, CAN oder den Testgenerator hinzufügen.")
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: AppTheme.borders.primary }
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 10
            spacing: 8
            Icon { name: "drop"; size: 14; color: AppTheme.text.hint }
            Label { text: qsTr("Signal auf ein Diagramm ziehen"); font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.hint; Layout.fillWidth: true; elide: Text.ElideRight }
            IconButton { iconName: "plus"; tip: qsTr("Signal manuell anlegen"); onClicked: root.addSignalRequested() }
        }
    }
}

// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4
import QtQuick.Shapes
import Theme 1.0

/** Chart type chooser that states which data each type needs before it is created. */
Dialog {
    id: root
    property var workspaceController
    property int typeIndex: 0
    property var chosenSignals: ({})
    signal requested(string chartType, string chartTitle, var signalIds)

    modal: true
    padding: 0
    width: Math.min(920, parent ? parent.width - 64 : 920)
    height: Math.min(640, parent ? parent.height - 64 : 640)

    readonly property var types: [
        { type: "time_series", name: qsTr("Zeitverlauf"), badge: "Y(t)", color: "#5EC2FF",
          text: qsTr("X-Achse ist die Zeit. Jeder Messwert als eigene Kurve."), needs: qsTr("Benötigt: Y"),
          path: "M4 28L14 12L24 30L34 6L44 24L54 14L64 30L74 10L80 18" },
        { type: "xy_line", name: qsTr("XY · Linie"), badge: "X ↔ Y", color: "#C79BFF",
          text: qsTr("Bahnkurve aus echten X/Y-Paaren in Empfangsreihenfolge."), needs: qsTr("Benötigt: X und Y im Paket"),
          path: "M16 30C16 4 66 4 66 18S28 36 44 18S72 8 78 14" },
        { type: "xy_scatter", name: qsTr("XY · Punkte"), badge: "X · Y", color: "#F2A65A",
          text: qsTr("Streuung ohne Verbindungslinie, z. B. Kennfelder."), needs: qsTr("Benötigt: X und Y im Paket"),
          path: "M18 24h.5M28 16h.5M34 28h.5M44 10h.5M50 20h.5M60 8h.5M66 18h.5M74 6h.5M38 14h.5M70 12h.5" },
        { type: "xyz_scatter", name: qsTr("XYZ · 3D"), badge: "X · Y · Z", color: "#9BD77E",
          text: qsTr("3D-Punktwolke. Grafikkartenabhängig, kleineres Punktlimit."), needs: qsTr("Benötigt: X, Y und Z"),
          path: "M36 18h.5M44 12h.5M32 26h.5M52 22h.5M60 10h.5M42 30h.5M66 16h.5" }
    ]

    onAboutToShow: { nameField.text = ""; chosenSignals = ({}); nameField.forceActiveFocus() }
    onAccepted: {
        var ids = []
        for (var id in chosenSignals) if (chosenSignals[id]) ids.push(id)
        requested(types[typeIndex].type, nameField.text.trim() || types[typeIndex].name, ids)
    }

    background: Rectangle { color: AppTheme.surfaces.dialog; border.color: AppTheme.borders.strong; radius: AppTheme.radius.extraLarge }

    header: Item {
        implicitHeight: 56
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.rightMargin: 12
            Label { text: qsTr("Diagramm erstellen"); font.pixelSize: AppTheme.fontSize.large; font.weight: Font.DemiBold; Layout.fillWidth: true }
            IconButton { iconName: "close"; tip: qsTr("Schließen"); onClicked: root.reject() }
        }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: AppTheme.borders.primary }
    }

    contentItem: ColumnLayout {
        spacing: 18
        Item { implicitHeight: 2 }
        Caption { text: qsTr("Was soll auf der X-Achse stehen?"); Layout.leftMargin: 24 }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: false  // cards fill the row height only, not the dialog
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            spacing: 12
            Repeater {
                model: root.types
                delegate: AbstractButton {
                    id: card
                    required property var modelData
                    required property int index
                    readonly property bool selected: root.typeIndex === index
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 1
                    implicitHeight: cardColumn.implicitHeight + 24
                    checkable: true
                    checked: selected
                    hoverEnabled: true
                    focusPolicy: Qt.StrongFocus
                    Accessible.role: Accessible.RadioButton
                    Accessible.name: modelData.name + ". " + modelData.needs
                    onClicked: root.typeIndex = index
                    background: Rectangle {
                        radius: AppTheme.radius.large
                        color: card.selected ? "#122130" : card.hovered ? AppTheme.surfaces.hover : AppTheme.surfaces.panel
                        border.width: card.visualFocus ? 2 : 1
                        border.color: card.visualFocus || card.selected ? AppTheme.palette.primary : AppTheme.borders.primary
                    }
                    contentItem: Item {
                        ColumnLayout {
                            id: cardColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 12
                            spacing: 8
                            Item {
                                Layout.fillWidth: true
                                implicitHeight: 76
                                Shape {
                                    width: 86; height: 36
                                    anchors.centerIn: parent
                                    scale: Math.min(2, parent.width / 90)
                                    preferredRendererType: Shape.CurveRenderer
                                    ShapePath {
                                        strokeColor: "#3A4556"; strokeWidth: 1; fillColor: "transparent"
                                        PathSvg { path: "M2 34H84M2 2V34" }
                                    }
                                    ShapePath {
                                        strokeColor: card.modelData.color
                                        strokeWidth: card.index >= 2 ? 4 : 2
                                        fillColor: "transparent"
                                        capStyle: ShapePath.RoundCap
                                        joinStyle: ShapePath.RoundJoin
                                        PathSvg { path: card.modelData.path }
                                    }
                                }
                            }
                            RowLayout {
                                spacing: 8
                                Label { text: card.modelData.name; font.weight: Font.DemiBold }
                                Label { text: card.modelData.badge; font.family: AppTheme.monoFamily; font.pixelSize: AppTheme.fontSize.caption; color: AppTheme.text.secondary }
                            }
                            Label { text: card.modelData.text; wrapMode: Text.WordWrap; font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.secondary; Layout.fillWidth: true }
                            Label { text: card.modelData.needs; font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.hint }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            spacing: 24
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.alignment: Qt.AlignTop
                spacing: 6
                Label { text: qsTr("Name"); font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.secondary }
                TextField {
                    id: nameField
                    Layout.fillWidth: true
                    placeholderText: root.types[root.typeIndex].name
                    maximumLength: 100
                    selectByMouse: true
                    Accessible.name: qsTr("Diagrammname")
                    onAccepted: root.accept()
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 12
                    implicitHeight: hint.implicitHeight + 24
                    radius: AppTheme.radius.large
                    color: AppTheme.surfaces.panel
                    border.color: AppTheme.borders.primary
                    RowLayout {
                        id: hint
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 10
                        Icon { name: "info"; color: AppTheme.text.hint; Layout.alignment: Qt.AlignTop }
                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: AppTheme.text.secondary
                            text: qsTr("Ein Zeitstempel wird nie als X-Messwert verwendet. Für „Messwert über Zeit“ Zeitverlauf wählen.")
                        }
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                spacing: 6
                RowLayout {
                    Label { text: qsTr("Signale direkt zuordnen"); font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.secondary; Layout.fillWidth: true }
                    Label { text: qsTr("optional"); font.pixelSize: AppTheme.fontSize.small; color: AppTheme.text.hint }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: AppTheme.radius.large
                    color: "transparent"
                    border.color: AppTheme.borders.primary
                    ListView {
                        id: signalList
                        anchors.fill: parent
                        anchors.margins: 4
                        clip: true
                        model: root.workspaceController ? root.workspaceController.signalModel : null
                        ScrollBar.vertical: ScrollBar {}
                        delegate: CheckDelegate {
                            id: pick
                            required property string uniqueId
                            required property string displayName
                            required property var color
                            width: signalList.width
                            height: 34
                            leftPadding: 28
                            text: displayName
                            checked: !!root.chosenSignals[uniqueId]
                            onToggled: {
                                var next = Object.assign({}, root.chosenSignals)
                                next[uniqueId] = checked
                                root.chosenSignals = next
                            }
                            Rectangle { x: 10; anchors.verticalCenter: parent.verticalCenter; width: 10; height: 10; radius: 2; color: pick.color }
                        }
                        Label {
                            anchors.centerIn: parent
                            visible: signalList.count === 0
                            text: qsTr("Noch keine Signale vorhanden.")
                            color: AppTheme.text.hint
                        }
                    }
                }
            }
        }
    }

    footer: Item {
        implicitHeight: 60
        Rectangle { width: parent.width; height: 1; color: AppTheme.borders.primary }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.rightMargin: 20
            spacing: 8
            Label { text: qsTr("Wird als Kachel neben die bestehenden Diagramme gesetzt."); color: AppTheme.text.hint; Layout.fillWidth: true; elide: Text.ElideRight }
            UiButton { text: qsTr("Abbrechen"); onClicked: root.reject() }
            UiButton {
                readonly property int picked: Object.keys(root.chosenSignals).filter(function(k) { return root.chosenSignals[k] }).length
                text: picked ? qsTr("Erstellen · %1 Signal(e)").arg(picked) : qsTr("Erstellen")
                variant: "primary"
                onClicked: root.accept()
            }
        }
    }
}

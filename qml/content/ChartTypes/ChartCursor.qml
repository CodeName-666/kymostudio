// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import Theme 1.0

/** Passive coordinate cursor. It observes hover without consuming pan/zoom. */
Item {
    id: root
    property var chartView
    property point point: Qt.point(0, 0)
    property bool insidePlot: enabled && hover.hovered && chartView &&
        hover.point.position.x >= chartView.plotArea.x &&
        hover.point.position.x <= chartView.plotArea.x + chartView.plotArea.width &&
        hover.point.position.y >= chartView.plotArea.y &&
        hover.point.position.y <= chartView.plotArea.y + chartView.plotArea.height
    z: 5
    HoverHandler {
        id: hover
        enabled: root.enabled
        onPointChanged: {
            if (root.chartView && root.chartView.count > 0)
                root.point = root.chartView.mapToValue(point.position, root.chartView.series(0))
        }
    }
    Rectangle {
        visible: root.insidePlot
        x: hover.point.position.x
        y: root.chartView ? root.chartView.plotArea.y : 0
        width: 1
        height: root.chartView ? root.chartView.plotArea.height : 0
        color: AppTheme.text.secondary
        opacity: 0.5
    }
    Rectangle {
        visible: root.insidePlot
        x: root.chartView ? root.chartView.plotArea.x : 0
        y: hover.point.position.y
        width: root.chartView ? root.chartView.plotArea.width : 0
        height: 1
        color: AppTheme.text.secondary
        opacity: 0.5
    }
    Label {
        visible: root.insidePlot
        x: Math.min(hover.point.position.x + 12, Math.max(0, root.width - width - 8))
        y: Math.max(8, hover.point.position.y - height - 8)
        text: "x " + Number(root.point.x).toPrecision(6) + "  ·  y " + Number(root.point.y).toPrecision(6)
        padding: 6
        font.pixelSize: 12
        color: AppTheme.text.primary
        background: Rectangle { color: AppTheme.surfaces.card; border.color: AppTheme.borders.primary; radius: 4 }
    }
}

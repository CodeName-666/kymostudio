import QtQuick 6.4
import "../FloatingWindows"

Item {
    id: root
    required property var workspaceController

    Repeater {
        model: root.workspaceController ? root.workspaceController.chartModel : null

        delegate: FloatingChartWindow {
            chartId: model.chartId
            chartType: model.chartType
            chartTitle: model.chartTitle
            x: model.xPos
            y: model.yPos
            width: model.windowWidth
            height: model.windowHeight
            isMaximized: model.maximized
            isMinimized: model.minimized
            restoreGeometry: Qt.rect(model.restoreX, model.restoreY, model.restoreWidth, model.restoreHeight)
            minimizeRestoreGeometry: Qt.rect(model.restoreX, model.restoreY, model.restoreWidth, model.restoreHeight)
            zOrder: model.zOrder
            isDocked: model.docked
            dockPosition: model.dockPosition
            workspaceController: root.workspaceController
        }
    }
}

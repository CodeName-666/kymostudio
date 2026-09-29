import QtQuick 6.4
import "content"
import QtCharts 2.3

import QtQuick.Window 2.15
import QtQuick.Controls 6.4
import QtQuick.Timeline 1.0
import QtCharts 2.3
import QtQuick.Layouts 1.15

//App {
//
//}

ApplicationWindow {
    id: window
    width: 640
    height: 480
    visible: true

    Flickable{
        id:flick
        anchors.fill: parent
        contentHeight: chartview.height
        contentWidth:  chartview.width
        ChartView {
            id: chartview
            width: window.width * 2
            height: window.height * 2
            LineSeries {
                name: "LineSeries"
                axisX: ValueAxis {
                    min: 0
                    //max: 200
                    tickCount: 12
                    labelFormat: "%.0f"
                }
                XYPoint { x: 0; y: 0.0 }
                XYPoint { x: 1.1; y: 3.2 }
                XYPoint { x: 1.9; y: 2.4 }
                XYPoint { x: 2.1; y: 2.1 }
                XYPoint { x: 2.9; y: 2.6 }
                XYPoint { x: 3.4; y: 2.3 }
                XYPoint { x: 200.1; y: 3.1 }
            }
        }

        ScrollBar.horizontal: ScrollBar {
            id: hbar
            hoverEnabled: true
            active: hovered || pressed
            orientation: Qt.Horizontal
        }
    }
}

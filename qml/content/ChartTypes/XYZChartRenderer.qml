import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick3D 6.4
import Theme 1.0

/**
 * XYZChartRenderer.qml
 *
 * 3D Chart renderer for floating windows.
 * Displays XYZ scatter plots with full camera controls (orbit, pan, zoom).
 *
 * Expected properties from parent FloatingChartWindow:
 * - chartId: Unique identifier for this chart instance
 * - chartTitle: Display name for the chart
 */
Item {
    id: root

    // Public properties that can be set by parent
    property string chartId: ""
    property string chartTitle: "3D Chart"
    property var chartData: null  // Reference to chart data model

    // 3D View configuration
    property real initialCameraDistance: 50
    property real initialCameraElevation: 30  // degrees
    property real initialCameraAzimuth: 45    // degrees

    // Current camera state
    property real cameraDistance: initialCameraDistance
    property real cameraElevation: initialCameraElevation
    property real cameraAzimuth: initialCameraAzimuth

    // Axis ranges
    property real xMin: -10
    property real xMax: 10
    property real yMin: -10
    property real yMax: 10
    property real zMin: -10
    property real zMax: 10

    property bool updatesSuspended: false
    property int maxPointsPerSeries: 5000

    // Internal state
    property var _scatterPlots: ({})  // Dictionary of scatter plots by uniqueId
    property var _pointModels: ({})   // Dictionary of point arrays by uniqueId

    // Reuse compiled components for every series and point.
    Component {
        id: scatterNodeComponent
        Node {
            property color pointColor: "#ffff00"
        }
    }

    Component {
        id: pointComponent
        Model {
            id: pointModel
            property color pointColor: "#ffff00"
            source: "#Sphere"
            scale: Qt.vector3d(0.3, 0.3, 0.3)
            materials: PrincipledMaterial {
                baseColor: pointModel.pointColor
                metalness: 0.3
                roughness: 0.5
            }
        }
    }

    // 3D View
    View3D {
        id: view3D
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: AppTheme.surfaces.interfaceBackground
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        // Main camera
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(
                cameraDistance * Math.cos(cameraElevation * Math.PI / 180) * Math.cos(cameraAzimuth * Math.PI / 180),
                cameraDistance * Math.sin(cameraElevation * Math.PI / 180),
                cameraDistance * Math.cos(cameraElevation * Math.PI / 180) * Math.sin(cameraAzimuth * Math.PI / 180)
            )

            eulerRotation.x: -cameraElevation
            eulerRotation.y: cameraAzimuth

            clipNear: 1
            clipFar: 1000
            fieldOfView: 60
        }

        // Directional light (main light)
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: 45
            brightness: 1.0
            castsShadow: false
        }

        // Ambient light
        DirectionalLight {
            eulerRotation.x: 30
            eulerRotation.y: -45
            brightness: 0.3
        }

        // Origin point
        Model {
            source: "#Sphere"
            scale: Qt.vector3d(0.2, 0.2, 0.2)
            position: Qt.vector3d(0, 0, 0)
            materials: PrincipledMaterial {
                baseColor: "#ff0000"
                metalness: 0.5
                roughness: 0.3
            }
        }

        // X Axis (Red)
        Model {
            id: xAxisLine
            source: "#Cylinder"
            position: Qt.vector3d((xMin + xMax) / 2, 0, 0)
            scale: Qt.vector3d(0.05, (xMax - xMin) / 2, 0.05)
            eulerRotation.z: 90
            materials: PrincipledMaterial {
                baseColor: "#ff0000"
                metalness: 0.3
                roughness: 0.5
            }
        }

        // Y Axis (Green)
        Model {
            id: yAxisLine
            source: "#Cylinder"
            position: Qt.vector3d(0, (yMin + yMax) / 2, 0)
            scale: Qt.vector3d(0.05, (yMax - yMin) / 2, 0.05)
            materials: PrincipledMaterial {
                baseColor: "#00ff00"
                metalness: 0.3
                roughness: 0.5
            }
        }

        // Z Axis (Blue)
        Model {
            id: zAxisLine
            source: "#Cylinder"
            position: Qt.vector3d(0, 0, (zMin + zMax) / 2)
            scale: Qt.vector3d(0.05, (zMax - zMin) / 2, 0.05)
            eulerRotation.x: 90
            materials: PrincipledMaterial {
                baseColor: "#0000ff"
                metalness: 0.3
                roughness: 0.5
            }
        }

        // Grid XY Plane (at Z=0)
        Repeater {
            model: 21
            Model {
                source: "#Cylinder"
                property real pos: -10 + index
                position: Qt.vector3d(pos, 0, 0)
                scale: Qt.vector3d(0.01, 10, 0.01)
                eulerRotation.z: 90
                materials: PrincipledMaterial {
                    baseColor: index === 10 ? "#555555" : "#333333"
                    metalness: 0
                    roughness: 1
                }
            }
        }

        Repeater {
            model: 21
            Model {
                source: "#Cylinder"
                property real pos: -10 + index
                position: Qt.vector3d(0, pos, 0)
                scale: Qt.vector3d(0.01, 10, 0.01)
                materials: PrincipledMaterial {
                    baseColor: index === 10 ? "#555555" : "#333333"
                    metalness: 0
                    roughness: 1
                }
            }
        }

        // Container for scatter plot points (will be populated dynamically)
        Node {
            id: scatterPlotContainer
        }

        // Mouse interaction area
        MouseArea {
            id: mouseArea3D
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
            hoverEnabled: true

            property real lastMouseX: 0
            property real lastMouseY: 0

            // Mouse wheel zoom
            onWheel: function(wheel) {
                var factor = wheel.angleDelta.y > 0 ? 0.9 : 1.1
                root.cameraDistance = Math.max(5, Math.min(200, root.cameraDistance * factor))
            }

            onPressed: function(mouse) {
                lastMouseX = mouse.x
                lastMouseY = mouse.y
            }

            onPositionChanged: function(mouse) {
                if (pressedButtons & Qt.LeftButton) {
                    // Orbit rotation
                    var deltaX = mouse.x - lastMouseX
                    var deltaY = mouse.y - lastMouseY

                    root.cameraAzimuth += deltaX * 0.5
                    root.cameraElevation = Math.max(-89, Math.min(89, root.cameraElevation - deltaY * 0.5))

                    lastMouseX = mouse.x
                    lastMouseY = mouse.y
                } else if (pressedButtons & Qt.RightButton) {
                    // Pan (not yet fully implemented - requires camera target)
                    lastMouseX = mouse.x
                    lastMouseY = mouse.y
                }
            }
        }
    }

    // Axis labels overlay (2D overlay on top of 3D view)
    Item {
        anchors.fill: parent

        Text {
            text: "X"
            color: "#ff0000"
            font.pixelSize: 16
            font.bold: true
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 10
        }

        Text {
            text: "Y"
            color: "#00ff00"
            font.pixelSize: 16
            font.bold: true
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 10
        }

        Text {
            text: "Z"
            color: "#0000ff"
            font.pixelSize: 16
            font.bold: true
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.rightMargin: 10
            anchors.topMargin: 10
        }
    }

    // Control panel overlay (top-right corner)
    Rectangle {
        id: controlPanel
        width: 220
        height: controlColumn.height + 20
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 10
        color: AppTheme.surfaces.card
        radius: 6
        opacity: 0.95
        border.color: AppTheme.borders.primary
        border.width: 1
        z: 100

        Column {
            id: controlColumn
            anchors.centerIn: parent
            spacing: 8
            width: parent.width - 20

            Text {
                text: "3D Camera Controls"
                color: AppTheme.text.primary
                font.pixelSize: 12
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Rectangle {
                width: parent.width
                height: 1
                color: AppTheme.borders.subtle
            }

            // Zoom controls
            Row {
                spacing: 5
                anchors.horizontalCenter: parent.horizontalCenter

                Text {
                    text: "Zoom:"
                    color: AppTheme.text.secondary
                    font.pixelSize: 11
                    anchors.verticalCenter: parent.verticalCenter
                }

                Button {
                    text: "+"
                    width: 35
                    height: 28
                    font.pixelSize: 14
                    onClicked: root.zoomIn()
                    ToolTip.text: "Zoom In"
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                }

                Button {
                    text: "-"
                    width: 35
                    height: 28
                    font.pixelSize: 14
                    onClicked: root.zoomOut()
                    ToolTip.text: "Zoom Out"
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                }

                Button {
                    text: "↺"
                    width: 35
                    height: 28
                    font.pixelSize: 14
                    onClicked: root.resetCamera()
                    ToolTip.text: "Reset Camera"
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                }
            }

            // View angle presets
            Text {
                text: "View Angle:"
                color: AppTheme.text.secondary
                font.pixelSize: 11
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Row {
                spacing: 5
                anchors.horizontalCenter: parent.horizontalCenter

                Button {
                    text: "Front"
                    width: 60
                    height: 28
                    font.pixelSize: 10
                    onClicked: root.setViewFront()
                    ToolTip.text: "Front View (XY)"
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                }

                Button {
                    text: "Top"
                    width: 60
                    height: 28
                    font.pixelSize: 10
                    onClicked: root.setViewTop()
                    ToolTip.text: "Top View (XZ)"
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                }

                Button {
                    text: "Side"
                    width: 60
                    height: 28
                    font.pixelSize: 10
                    onClicked: root.setViewSide()
                    ToolTip.text: "Side View (YZ)"
                    ToolTip.visible: hovered
                    ToolTip.delay: 500
                }
            }

            // Orbit controls
            Text {
                text: "Orbit:"
                color: AppTheme.text.secondary
                font.pixelSize: 11
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Grid {
                columns: 3
                spacing: 5
                anchors.horizontalCenter: parent.horizontalCenter

                Item { width: 35; height: 28 }
                Button {
                    text: "↑"
                    width: 35
                    height: 28
                    onClicked: root.orbitUp()
                }
                Item { width: 35; height: 28 }

                Button {
                    text: "←"
                    width: 35
                    height: 28
                    onClicked: root.orbitLeft()
                }
                Button {
                    text: "⊙"
                    width: 35
                    height: 28
                    onClicked: root.resetCamera()
                    ToolTip.text: "Center"
                    ToolTip.visible: hovered
                }
                Button {
                    text: "→"
                    width: 35
                    height: 28
                    onClicked: root.orbitRight()
                }

                Item { width: 35; height: 28 }
                Button {
                    text: "↓"
                    width: 35
                    height: 28
                    onClicked: root.orbitDown()
                }
                Item { width: 35; height: 28 }
            }

            // Camera info
            Rectangle {
                width: parent.width
                height: 1
                color: AppTheme.borders.subtle
            }

            Text {
                text: "Distance: " + root.cameraDistance.toFixed(1)
                color: AppTheme.text.secondary
                font.pixelSize: 10
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "Elevation: " + root.cameraElevation.toFixed(1) + "°"
                color: AppTheme.text.secondary
                font.pixelSize: 10
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "Azimuth: " + root.cameraAzimuth.toFixed(1) + "°"
                color: AppTheme.text.secondary
                font.pixelSize: 10
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    /*******************************************************************
     * PUBLIC FUNCTIONS - Camera Controls
     ******************************************************************/

    /**
     * Zoom in by 20%
     */
    function zoomIn() {
        root.cameraDistance = Math.max(5, root.cameraDistance * 0.8)
    }

    /**
     * Zoom out by 25%
     */
    function zoomOut() {
        root.cameraDistance = Math.min(200, root.cameraDistance * 1.25)
    }

    /**
     * Reset camera to initial position
     */
    function resetCamera() {
        root.cameraDistance = root.initialCameraDistance
        root.cameraElevation = root.initialCameraElevation
        root.cameraAzimuth = root.initialCameraAzimuth
    }

    /**
     * Orbit camera left (decrease azimuth)
     */
    function orbitLeft() {
        root.cameraAzimuth -= 15
    }

    /**
     * Orbit camera right (increase azimuth)
     */
    function orbitRight() {
        root.cameraAzimuth += 15
    }

    /**
     * Orbit camera up (increase elevation)
     */
    function orbitUp() {
        root.cameraElevation = Math.min(89, root.cameraElevation + 15)
    }

    /**
     * Orbit camera down (decrease elevation)
     */
    function orbitDown() {
        root.cameraElevation = Math.max(-89, root.cameraElevation - 15)
    }

    /**
     * Set camera to front view (looking at XY plane)
     */
    function setViewFront() {
        root.cameraElevation = 0
        root.cameraAzimuth = 0
        root.cameraDistance = 30
    }

    /**
     * Set camera to top view (looking down at XZ plane)
     */
    function setViewTop() {
        root.cameraElevation = 89
        root.cameraAzimuth = 0
        root.cameraDistance = 30
    }

    /**
     * Set camera to side view (looking at YZ plane)
     */
    function setViewSide() {
        root.cameraElevation = 0
        root.cameraAzimuth = 90
        root.cameraDistance = 30
    }

    /*******************************************************************
     * PUBLIC FUNCTIONS - Scatter Plot Management
     ******************************************************************/

    /**
     * Create a new 3D scatter plot
     * @param uniqueId - Unique identifier for the scatter plot
     * @param displayName - Display name for the scatter plot
     * @param color - Point color (hex string)
     * @return Scatter plot container node
     */
    function createScatterPlot(uniqueId, displayName, color) {
        if (_scatterPlots[uniqueId]) {
            console.warn("XYZChartRenderer: Scatter plot already exists: " + uniqueId)
            return _scatterPlots[uniqueId]
        }

        var scatterNode = scatterNodeComponent.createObject(scatterPlotContainer, {
            "objectName": displayName,
            "pointColor": color || "#ffff00"
        })
        if (!scatterNode) {
            console.error("XYZChartRenderer: Could not create scatter plot " + uniqueId)
            return null
        }

        _scatterPlots[uniqueId] = scatterNode
        _pointModels[uniqueId] = []

        console.log("XYZChartRenderer: Created scatter plot '" + displayName + "' with ID " + uniqueId)
        return scatterNode
    }

    /**
     * Create/register a new scatter plot line for this chart (called by ChartWindow assignment)
     */
    function createLine(uniqueId, displayName, color, interfaceType, dataId) {
        var node = createScatterPlot(uniqueId, displayName, color)

        return node
    }

    function removeLine(uniqueId) {
        removeScatterPlot(uniqueId)
        return true
    }

    function getLine(uniqueId) {
        return _scatterPlots[uniqueId] || null
    }

    function updateLineProperties(uniqueId, valueField, displayName, color, visible) {
        var node = _scatterPlots[uniqueId]
        if (!node) return
        node.objectName = displayName
        node.pointColor = color
        node.visible = visible
        var points = _pointModels[uniqueId] || []
        for (var i = 0; i < points.length; i++) {
            points[i].pointColor = color
        }
    }

    /**
     * Append a single 3D point to a scatter plot
     * @param uniqueId - Scatter plot identifier
     * @param x - X coordinate
     * @param y - Y coordinate
     * @param z - Z coordinate
     */
    function appendPoint3D(uniqueId, x, y, z) {
        if (root.updatesSuspended) return
        if (!_scatterPlots[uniqueId]) return
        var scatterNode = _scatterPlots[uniqueId]
        var pointColor = (scatterNode && scatterNode.pointColor !== undefined) ? scatterNode.pointColor : "#ffff00"

        var point = pointComponent.createObject(_scatterPlots[uniqueId], {
            "position": Qt.vector3d(x, y, z),
            "pointColor": pointColor
        })
        if (point) {
            _pointModels[uniqueId].push(point)

            // Limit maximum points for performance
            if (_pointModels[uniqueId].length > root.maxPointsPerSeries) {
                var oldPoint = _pointModels[uniqueId].shift()
                oldPoint.destroy()
            }
        }
    }

    /**
     * Append multiple 3D points at once (BATCH - much faster!)
     * @param uniqueId - Scatter plot identifier
     * @param points - Array of [x, y, z] tuples
     */
    function appendPointsBatch3D(uniqueId, points) {
        if (root.updatesSuspended) return
        if (!_scatterPlots[uniqueId]) return

        if (!points || points.length === 0) {
            return
        }

        var maxPoints = root.maxPointsPerSeries
        var totalAfterAdd = _pointModels[uniqueId].length + points.length

        // Remove old points if necessary
        if (totalAfterAdd > maxPoints) {
            var toRemove = totalAfterAdd - maxPoints
            for (var i = 0; i < toRemove; i++) {
                var oldPoint = _pointModels[uniqueId].shift()
                if (oldPoint) {
                    oldPoint.destroy()
                }
            }
        }

        // Batch create points (more efficient than individual creation)
        for (var j = 0; j < points.length; j++) {
            var p = points[j]
            appendPoint3D(uniqueId, p[0], p[1], p[2])
        }

    }

    /**
     * Clear all points from a scatter plot
     * @param uniqueId - Scatter plot identifier
     */
    function clearPoints(uniqueId) {
        if (!_pointModels[uniqueId]) {
            return
        }

        // Destroy all point models
        for (var i = 0; i < _pointModels[uniqueId].length; i++) {
            _pointModels[uniqueId][i].destroy()
        }
        _pointModels[uniqueId] = []
    }

    /**
     * Remove a scatter plot
     * @param uniqueId - Unique identifier of the scatter plot to remove
     */
    function removeScatterPlot(uniqueId) {
        if (_scatterPlots[uniqueId]) {
            clearPoints(uniqueId)
            _scatterPlots[uniqueId].destroy()
            delete _scatterPlots[uniqueId]
            delete _pointModels[uniqueId]
            console.log("XYZChartRenderer: Removed scatter plot " + uniqueId)
        }
    }

    /**
     * Clear all scatter plots
     */
    function clearAll() {
        for (var plotId in _scatterPlots) {
            clearPoints(plotId)
        }
    }

    /**
     * Update axis ranges based on data
     * @param minX, maxX, minY, maxY, minZ, maxZ - New axis ranges
     */
    function updateAxisRanges(minX, maxX, minY, maxY, minZ, maxZ) {
        root.xMin = minX
        root.xMax = maxX
        root.yMin = minY
        root.yMax = maxY
        root.zMin = minZ
        root.zMax = maxZ
    }

    /*******************************************************************
     * COMPONENT LIFECYCLE
     ******************************************************************/

    Component.onCompleted: {
        console.log("XYZChartRenderer initialized for chart: " + root.chartId)
    }

    Component.onDestruction: {
        console.log("XYZChartRenderer destroyed for chart: " + root.chartId)
        // Cleanup all scatter plots
        for (var plotId in _scatterPlots) {
            removeScatterPlot(plotId)
        }
    }

}

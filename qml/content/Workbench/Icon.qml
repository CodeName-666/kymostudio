import QtQuick 6.4
import QtQuick.Shapes
import Theme 1.0

/** Stroke icon drawn on a 16×16 grid; `name` selects the path, `color` follows text. */
Item {
    id: root
    property string name: ""
    property color color: AppTheme.text.secondary
    property real size: 16
    implicitWidth: size
    implicitHeight: size

    readonly property var paths: ({
        plus: "M8 3v10M3 8h10",
        play: "M5 3.5L12 8L5 12.5Z",
        pause: "M6 4v8M10 4v8",
        stop: "M4.5 4h7v8h-7Z",
        close: "M4.5 4.5l7 7M11.5 4.5l-7 7",
        download: "M8 2.5v8M4.5 7L8 10.5L11.5 7M3 13.5h10",
        settings: "M3 4.5h1.5M7.5 4.5H13M3 11.5h6M12 11.5h1M4.5 4.5a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0 -3 0M9 11.5a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0 -3 0",
        search: "M2.5 7a4.5 4.5 0 1 0 9 0a4.5 4.5 0 1 0 -9 0M10.5 10.5l3 3",
        fit: "M2.5 6V2.5H6M10 2.5h3.5V6M13.5 10v3.5H10M6 13.5H2.5V10",
        more: "M2.7 8a.8 .8 0 1 0 1.6 0a.8 .8 0 1 0 -1.6 0M7.2 8a.8 .8 0 1 0 1.6 0a.8 .8 0 1 0 -1.6 0M11.7 8a.8 .8 0 1 0 1.6 0a.8 .8 0 1 0 -1.6 0",
        chevronDown: "M4 6l4 4l4 -4",
        chevronRight: "M6 4l4 4l-4 4",
        pencil: "M10.5 3L13 5.5L6 12.5H3.5V10Z",
        trash: "M3 4.5h10M6.5 4.5V3h3v1.5M4.5 4.5l.7 8.5h5.6l.7 -8.5",
        check: "M3.5 8.5l3 3l6 -7",
        warning: "M8 2.5L14 13H2ZM8 6.5V9M8 11v.5",
        info: "M2 8a6 6 0 1 0 12 0a6 6 0 1 0 -12 0M8 7v4M8 5v.5",
        error: "M2 8a6 6 0 1 0 12 0a6 6 0 1 0 -12 0M8 5v3.5M8 10.5v.5",
        tiles: "M2 2h12v5H2ZM2 9h5v5H2ZM9 9h5v5H9Z",
        focus: "M2 2h12v12H2Z",
        free: "M2 2h8v7H2ZM6 7h8v7H6Z",
        clock: "M2.5 8a5.5 5.5 0 1 0 11 0a5.5 5.5 0 1 0 -11 0M8 5v3l2 1.5",
        refresh: "M13 8a5 5 0 1 1 -1.5 -3.5M13 3v2.5h-2.5",
        drop: "M8 3v7M5 7l3 3l3 -3M2.5 11h11v2.5h-11Z",
        logo: "M1.5 4.5a3 3 0 0 1 3 -3h7a3 3 0 0 1 3 3v7a3 3 0 0 1 -3 3h-7a3 3 0 0 1 -3 -3ZM3.5 10L6 6L8.5 9L12.5 4.5",
        image: "M2 3h12v10H2ZM2 11l4 -4l3 3l2 -2l3 3",
        folder: "M2 12.5V3.5h4l1.5 1.5H14v7.5Z",
        minimize: "M3.5 12.5h9",
        blocked: "M2 8a6 6 0 1 0 12 0a6 6 0 1 0 -12 0M4 12L12 4"
    })

    Shape {
        width: 16
        height: 16
        scale: root.size / 16
        transformOrigin: Item.TopLeft
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: root.color
            strokeWidth: 1.6
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: root.paths[root.name] || "" }
        }
    }
}

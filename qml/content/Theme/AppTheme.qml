pragma Singleton
pragma ComponentBehavior: Bound
import QtQuick 6.4

/** Design tokens of the workbench (see design canvas "Tokens & Komponenten"). */
QtObject {
    id: theme

    property bool showLegend: true
    property bool showGrid: true
    property bool showCrosshair: true
    property bool antialiasing: false
    property int displayPointLimit: 10000

    // Plex is preferred when installed; otherwise the platform UI font is used.
    readonly property string fontFamily: Qt.platform.os === "windows" ? "Segoe UI" : "IBM Plex Sans"
    readonly property string monoFamily: Qt.platform.os === "windows" ? "Consolas" : "IBM Plex Mono"

    readonly property var seriesColors: ["#5EC2FF", "#F2A65A", "#9BD77E", "#C79BFF", "#E78AB8", "#F2E27A"]

    readonly property QtObject palette: QtObject {
        readonly property color primary: "#4DB6F0"
        readonly property color primaryHover: "#6BC3F3"
        readonly property color primaryPressed: "#3AA3DD"
        readonly property color primaryBorder: "#2B5878"
        readonly property color primarySoft: "#13283A"
        readonly property color primaryText: "#06121B"
        readonly property color accent: "#4DB6F0"
        readonly property color danger: "#EF6F6C"
        readonly property color success: "#46C489"
        readonly property color warning: "#EDB248"
        readonly property color idle: "#4A5566"
    }

    // Tinted state surfaces: background, border, text.
    readonly property QtObject tone: QtObject {
        readonly property QtObject live: QtObject { readonly property color bg: "#10231A"; readonly property color border: "#1F4A34"; readonly property color text: "#9BE0BC" }
        readonly property QtObject warning: QtObject { readonly property color bg: "#2A2210"; readonly property color border: "#5A4719"; readonly property color text: "#F5D9A0" }
        readonly property QtObject danger: QtObject { readonly property color bg: "#2A1515"; readonly property color border: "#5C2626"; readonly property color text: "#F6C3C1" }
        readonly property QtObject neutral: QtObject { readonly property color bg: "#1B222C"; readonly property color border: "#313B48"; readonly property color text: "#A3AEBF" }
    }

    readonly property QtObject surfaces: QtObject {
        readonly property color background: "#0B0F14"
        readonly property color panel: "#11161D"
        readonly property color interfaceBackground: "#11161D"
        readonly property color dialog: "#151B23"
        readonly property color card: "#151B23"
        readonly property color control: "#1B222C"
        readonly property color controlHover: "#222A35"
        readonly property color hover: "#161C24"
        readonly property color muted: "#0B0F14"
        readonly property color plotGrid: "#1C232D"
    }

    readonly property QtObject borders: QtObject {
        readonly property color primary: "#252D38"
        readonly property color subtle: "#1E2630"
        readonly property color strong: "#313B48"
        readonly property color focus: palette.primary
        readonly property color danger: palette.danger
        readonly property color disabled: "#313B48"
    }

    readonly property QtObject text: QtObject {
        readonly property color primary: "#E7ECF3"
        readonly property color secondary: "#A3AEBF"
        readonly property color hint: "#7D899B"
        readonly property color label: "#C9D2DE"
        readonly property color contrast: "#06121B"
        readonly property color disabled: "#5E6A7B"
        readonly property color placeholder: "#7D899B"
    }

    readonly property QtObject states: QtObject {
        readonly property color disabledBackground: "#1B222C"
    }

    readonly property QtObject inputs: QtObject {
        readonly property color background: "#0B0F14"
        readonly property color disabledBackground: "#11161D"
    }

    readonly property QtObject buttons: QtObject {
        readonly property QtObject neutral: QtObject {
            readonly property color background: "#1B222C"
            readonly property color hover: "#222A35"
            readonly property color pressed: "#252D38"
            readonly property color border: "#313B48"
            readonly property color text: "#E7ECF3"
        }
    }

    readonly property QtObject spacing: QtObject {
        readonly property int small: 8
        readonly property int medium: 12
        readonly property int large: 16
        readonly property int extraLarge: 24
    }

    readonly property QtObject heights: QtObject {
        readonly property int control: 30
        readonly property int input: 30
        readonly property int button: 30
        readonly property int combobox: 30
        readonly property int smallInput: 26
        readonly property int label: 30
        readonly property int header: 48
        readonly property int statusBar: 28
        readonly property int chartHeader: 40
    }

    readonly property QtObject radius: QtObject {
        readonly property int small: 4
        readonly property int medium: 6
        readonly property int large: 8
        readonly property int extraLarge: 12
    }

    readonly property QtObject fontSize: QtObject {
        readonly property int caption: 11
        readonly property int small: 12
        readonly property int medium: 13
        readonly property int large: 16
        readonly property int title: 28
        readonly property int header: 16
        readonly property int button: 13
    }

    readonly property QtObject margins: QtObject {
        readonly property int small: 8
        readonly property int medium: 12
        readonly property int large: 16
        readonly property int extraLarge: 24
    }

    function chartTypeBadge(type) {
        switch (type) {
        case "time_series": return "Y(t)"
        case "xy_line": return "XY"
        case "xy_scatter": return "XY ·"
        case "xyz_scatter": return "XYZ"
        default: return "?"
        }
    }
    function chartTypeName(type) {
        switch (type) {
        case "time_series": return qsTr("Zeitverlauf")
        case "xy_line": return qsTr("XY · Linie")
        case "xy_scatter": return qsTr("XY · Punkte")
        case "xyz_scatter": return qsTr("XYZ · 3D")
        default: return type
        }
    }
    function chartTypeBadgeColors(type) {
        if (type === "time_series") return ["#13283A", "#8FD0F6"]
        if (type === "xyz_scatter") return ["#1D2C18", "#BDE6A8"]
        if (type === "xy_scatter") return ["#2E2214", "#F5C28D"]
        return ["#2A2140", "#D5BCFF"]
    }
}

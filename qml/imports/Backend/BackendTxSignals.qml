import QtQuick 6.6

QtObject {
    // QML -> Backend signals (to be wired to backend slots)
    signal connectTo(string connection_type)
    signal set_settings(string interface_type, var settings)
    signal set_plot_area(var area)
    signal set_axis(var xAxis, var yAxis)
    signal add_graph(var name, var graph)
}

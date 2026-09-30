import QtQuick 6.6

QtObject {
    // Backend -> QML signals (mirror of backend.py emits)
    signal newGraph(var uniqueId, var displayName, var color, var interfaceType)
    signal append_graph_point(var name, var point)
    signal append_graph_points_batch(var uniqueId, var points)
    signal append_graph_point_3d(var uniqueId, var point)
    signal append_graph_points_batch_3d(var uniqueId, var points)
    // High-level message update (for Messages table / inspection)
    signal message_received(var message)
    signal signals_removed(var uniqueIds)
    signal com_port_update(var portList)
    signal ui_setup(var settings)
    signal status_message(var level, var message)
}

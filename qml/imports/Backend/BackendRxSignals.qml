// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.6

QtObject {
    // Backend -> QML signals (mirror of backend.py emits)
    signal newGraph(var uniqueId, var displayName, var color, var interfaceType)
    signal append_graph_points_batch(var uniqueId, var points)
    signal append_graph_points_batch_3d(var uniqueId, var points)
    signal signals_removed(var uniqueIds)
    signal com_port_update(var portList)
    signal ui_setup(var settings)
    signal status_message(var level, var message)
}

// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Layouts 6.4
import Theme 1.0

/** Dialog button bar with a top divider; children are laid out left to right. */
Item {
    default property alias content: row.data
    implicitHeight: 56
    Rectangle { width: parent.width; height: 1; color: AppTheme.borders.primary }
    RowLayout {
        id: row
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 16
        spacing: 8
    }
}

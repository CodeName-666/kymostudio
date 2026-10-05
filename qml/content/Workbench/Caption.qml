// SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
// Copyright (c) 2026 Christof Seidel
import QtQuick 6.4
import QtQuick.Controls 6.4
import Theme 1.0

/** Small uppercase section label. */
Label {
    font.pixelSize: AppTheme.fontSize.caption
    font.weight: Font.DemiBold
    font.letterSpacing: 0.6
    font.capitalization: Font.AllUppercase
    color: AppTheme.text.hint
}

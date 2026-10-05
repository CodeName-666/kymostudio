import QtQuick 6.4
import QtQuick.Layouts 6.4

/** Titled group of FieldRows. */
ColumnLayout {
    property alias title: caption.text
    default property alias content: body.data
    Layout.fillWidth: true
    spacing: 10
    Caption { id: caption }
    ColumnLayout { id: body; Layout.fillWidth: true; spacing: 10 }
}

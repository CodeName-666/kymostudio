.pragma library
.import QtQuick 6.6 as QtQuick
.import "./Constants.js" as Constants

var backendEvents = null

function create_backend_events() {
    var component = Qt.createComponent(Qt.resolvedUrl(Constants.RX_SIGNAL_PATH))
    if (component.status === QtQuick.Component.Ready) {
        var obj = component.createObject(Qt.application)
        if (obj === null) {
            console.error("Backend events object could not be created")
        }
        return obj
    } else if (component.status === QtQuick.Component.Error) {
        console.error("Backend events component error:", component.errorString())
    } else {
        console.error("Backend events component not ready:", component.status)
    }
    return null
}

function get_backend_events() {
    if (backendEvents === null) {
        backendEvents = create_backend_events()
    }
    return backendEvents
}

function reset_backend_events() {
    if (backendEvents !== null) {
        backendEvents.destroy()
        backendEvents = null
    }
}

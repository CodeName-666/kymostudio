.pragma library

/*******************************************************************
 * FUNCTION
 ******************************************************************/
function Timer(parent, interval, start = false, repeat = false, callback = undefined) {

    var cTimer = Qt.createQmlObject(' import QtQuick 6.4; Timer {}',parent);

    cTimer.interval = interval
    cTimer.repeat = repeat

    if (callback !== undefined) {
        cTimer.triggered.connect(callback)
    }

    if (start) {
        cTimer.start()
    }

    return cTimer

}

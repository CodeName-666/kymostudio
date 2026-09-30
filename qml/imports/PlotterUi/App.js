.pragma library
.import QtQuick 6.6 as QtQuick
.import "../Common/AppApi.js" as AppApi


var app = undefined


function create()
{
    if(app === undefined)
    {
        app = new AppClass()
    }
    else
    {
        //Already created...
    }

    return app
}


function get_app()
{
    return app
}

class AppClass {

    constructor()
    {
        this.ui_handle = undefined
        this.used_backend_interface = undefined
        this.backend_events = undefined
    }

    setup(app_handle, backend_interface)
    {
        this.ui_handle = app_handle
        this.used_backend_interface = backend_interface
        // shared Rx interface for backend->QML signals
        this.backend_events = AppApi.get_backend_events()
        if(backend_interface && typeof backend_interface.setup === "function")
            backend_interface.setup(this.ui_handle, this.backend_events)
    }

    events()
    {
        return this.backend_events
    }
}

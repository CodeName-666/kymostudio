.pragma library
.import QtQuick 6.6 as QtQuick
.import "../Common/Constants.js" as Constants
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
        this.backend_tx_events = undefined
        this.backend_rx_events = undefined
        this.backend_events = undefined
        this.current_interface = undefined
    }

    setup(app_handle,backend_interface)
    {
        this.ui_handle = app_handle
        this.used_backend_interface = backend_interface
        // shared Rx interface for backend->QML signals
        this.backend_events = AppApi.get_backend_events()
        // Tx interface for QML->backend slots
        this.backend_tx_events = this.create_component(Constants.TX_SIGNAL_PATH)
        this.backend_rx_events = this.backend_events
        this.initialize()
    }

    create_component(path_to_component) {
        var events = undefined;
        var component = Qt.createComponent(path_to_component);
        if (component.status === QtQuick.Component.Ready) {
            events = component.createObject(this.ui_handle);
            if (!events) {
                console.error("Fehler: Objekt konnte nicht erstellt werden für", path_to_component);
            }
        } else if (component.status === QtQuick.Component.Error) {
            console.error("Fehler beim Laden der Komponente:", component.errorString());
        } else {
            console.error("Undefinierter Status beim Laden der Komponente:", path_to_component);
        }
        return events;
    }

    initialize()
    {
        if(this.used_backend_interface !== undefined && this.used_backend_interface !== null)
        {
            if(typeof this.used_backend_interface.setup === "function")
            {
                this.used_backend_interface.setup(this.ui_handle, this.backend_events)
            }
        }
        this.connect_tx_to_backend()
        // reserved for future signal connections between tx/rx events
    }

    connect_tx_to_backend()
    {
        if(!this.backend_tx_events || !this.used_backend_interface)
            return
        const b = this.used_backend_interface
        const tx = this.backend_tx_events
        if(tx.connectTo && typeof b.connectTo === "function")
            tx.connectTo.connect(function(connection_type){ b.connectTo(connection_type) })
        if(tx.set_settings && typeof b.set_settings === "function")
            tx.set_settings.connect(function(interface_type, settings){ b.set_settings(interface_type, settings) })
        if(tx.set_plot_area && typeof b.set_plot_area === "function")
            tx.set_plot_area.connect(function(area){ b.set_plot_area(area) })
        if(tx.set_axis && typeof b.set_axis === "function")
            tx.set_axis.connect(function(xAxis, yAxis){ b.set_axis(xAxis, yAxis) })
        if(tx.add_graph && typeof b.add_graph === "function")
            tx.add_graph.connect(function(name, graph){ b.add_graph(name, graph) })
    }

    events()
    {
        return this.backend_events
    }

    connect()
    {
        if(!this.used_backend_interface)
        {
            console.warn("AppController: No backend available for connect()")
            return false
        }
        var connection_type = this.current_interface !== undefined ? this.current_interface : ""
        console.log("AppController: Attempting to connect with interface:", connection_type)

        if(!connection_type || connection_type === "")
        {
            console.error("AppController: No interface selected! current_interface is:", this.current_interface)
            return false
        }

        if(this.backend_tx_events && this.backend_tx_events.connectTo)
        {
            console.log("AppController: Calling backend_tx_events.connectTo with:", connection_type)
            this.backend_tx_events.connectTo(connection_type)
            return true
        }
        if(typeof this.used_backend_interface.connectTo === "function")
        {
            console.log("AppController: Calling used_backend_interface.connectTo with:", connection_type)
            return this.used_backend_interface.connectTo(connection_type)
        }
        if(typeof this.used_backend_interface.connect === "function")
        {
            console.log("AppController: Calling used_backend_interface.connect()")
            return this.used_backend_interface.connect()
        }
        console.warn("AppController: Backend does not implement connect/connectTo")
        return false
    }

    disconnect()
    {
        if(!this.used_backend_interface)
        {
            console.warn("AppController: No backend available for disconnect()")
            return false
        }
        var connection_type = this.current_interface !== undefined ? this.current_interface : ""
        if(!connection_type || connection_type === "")
        {
            console.error("AppController: No interface selected for disconnect()")
            return false
        }
        if(typeof this.used_backend_interface.disconnectFrom === "function")
            return this.used_backend_interface.disconnectFrom(connection_type)
        console.warn("AppController: Backend does not implement disconnectFrom")
        return false
    }

    set_settings(interface_type, settings)
    {
        console.log("AppController: updating settings for", interface_type)
        this.current_interface = interface_type
        console.log("AppController: current_interface set to:", this.current_interface)

        if(this.used_backend_interface && typeof this.used_backend_interface.set_settings === "function")
        {
            if(this.backend_tx_events && this.backend_tx_events.set_settings)
            {
                console.log("AppController: Calling backend_tx_events.set_settings")
                this.backend_tx_events.set_settings(interface_type, settings)
            }
            else
            {
                console.log("AppController: Calling used_backend_interface.set_settings directly")
                return this.used_backend_interface.set_settings(interface_type, settings)
            }
            return true
        }
        console.warn("AppController: Backend does not implement set_settings")
        return false
    }

    settings_valid()
    {
        if(this.used_backend_interface && typeof this.used_backend_interface.settings_valid === "function")
        {
            return this.used_backend_interface.settings_valid()
        }
        console.warn("AppController: Backend does not implement settings_valid")
        return false
    }

    set_plot_area(area)
    {
        if(this.backend_tx_events && this.backend_tx_events.set_plot_area)
            this.backend_tx_events.set_plot_area(area)
        else if(this.used_backend_interface && typeof this.used_backend_interface.set_plot_area === "function")
            this.used_backend_interface.set_plot_area(area)
    }

    set_axis(xAxis, yAxis)
    {
        if(this.backend_tx_events && this.backend_tx_events.set_axis)
            this.backend_tx_events.set_axis(xAxis, yAxis)
        else if(this.used_backend_interface && typeof this.used_backend_interface.set_axis === "function")
            this.used_backend_interface.set_axis(xAxis, yAxis)
    }

    add_graph(name, graph)
    {
        if(this.backend_tx_events && this.backend_tx_events.add_graph)
            this.backend_tx_events.add_graph(name, graph)
        else if(this.used_backend_interface && typeof this.used_backend_interface.add_graph === "function")
            this.used_backend_interface.add_graph(name, graph)
    }
}




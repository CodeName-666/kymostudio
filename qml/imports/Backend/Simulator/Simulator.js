.pragma library
.import QtQuick 6.4 as Quick
.import QtQml 2.15 as Qml
.import QtCharts 2.3 as QuickCharts

.import "../BackendLogger.js" as Logger
.import "../../Common/DataGen.js" as Data
.import "../../Common/Timer.js" as Timer



//--- Simulator Setup ----
var application_handle = undefined
var backend_events = undefined
var update_timer = undefined // Cycle Timer (equal Thread) as Mainloop for the Chart
var setup_done_status = false // Setup flag to verify is setup was done
var ui_setup_done = false

var timer_frequency = 0
var timer_counter = 0

var plot_area = undefined
var xAxis = undefined
var yAxis = undefined
var tick_points = 9

//--- UI/Backend parameter
var current_settings = undefined
var current_interface = undefined

var signal_list = {} // Dictionary of demo signals/Lines in the chart
var connected = false

//--- Demo Lines Config ---
var DEMO_LINE_CONFIG = [/*{
    "name": "DEMO_1",
    "color": 0xffffff,
    "type": "Sinus"
},
{
    "name": "DEMO_2",
    "color": 0xffffff,
    "type": "Sinus"
}*/]

var connection_interfaces = ["Test"]

var simulator_settings = {
    "interfaces": connection_interfaces
}

class Simulator {
    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    setup(app, events) {
        application_handle = app;
        setup_done_status = true
        connect_events(events);

        backend_events.ui_setup(simulator_settings)
        Logger.log_debug("SIMULATOR setup done")
    }

    /*******************************************************************
     * INTERNAL FUNCTION
     ******************************************************************/
    connect_events(events) {
        backend_events = events

    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    backend_simulator_loop() {

        backend_simulator_test_loop()
        update_time_count();
    }

    update_time_count() {
        timer_counter++;
    }


    get_run_time() {
        return timer_counter * 1 / timer_frequency;
    }

    get_frequency() {
        return timer_frequency;
    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    backend_simulator_test_loop() {

        let xPoint = plot_area.width / xAxis.tickCount;
        let yPoint = (xAxis.max - xAxis.min) / xAxis.tickCount

        for (const [key, value] of Object.entries(signal_list)) {
            let x = get_run_time();
            switch (value["type"]) {
                case "Sinus":
                    let f = get_frequency();
                    let y = Data.sinus(x, 1000, 2, 0, 5);

                    //console.log("Sinus = ", y)
                    value["graph"].append(tick_points, y);
                    break;
                case "Rectangle":

                    break;
            }
        }
        tick_points += yPoint
        // backend_events.scrollRight(xPoint)

    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    create_demo_lines() {


        DEMO_LINE_CONFIG.push({
            "name": current_settings["name"],
            "color": current_settings["color"],
            "type": current_settings["type"]
        })

        for (let i = 0; i < DEMO_LINE_CONFIG.length; i++) {
            let s = DEMO_LINE_CONFIG[i]
            backend_events.newGraph(s["name"], s["color"])
        }
    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    set_settings(type, settings) {
        current_settings = settings
        current_interface = type
        return true
    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    connect() {
        if (!is_connected()) {
            let time = 100;
            Logger.log_debug("Connect to interface: " + current_interface)
            if (current_interface === "Test") {

                if (settings_valid()) {
                    connected = true;
                    create_demo_lines();
                    update_timer = new Timer.Timer(application_handle, time, true, true, backend_simulator_loop)
                    timer_frequency = 1 / ((time + 50) / 1000)
                }
            }
            else {
                Logger.log_warning("No simulation avalilable.")
            }
        }
    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    get_settings(interface_type) {
        return current_settings
    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    get_interface() {
        return current_interface
    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    settings_valid() {
        if (current_settings !== undefined && current_interface !== undefined) {
            return true
        } else {
            return false
        }
    }

    /*******************************************************************
     * FUNCTION SLOT
     ******************************************************************/
    log_error(msg) {
        console.log("- ERROR - " + msg);
    }

    /*******************************************************************
     * FUNCTION SLOT
     ******************************************************************/
    log_warning(msg) {
        console.log("- WARNING - " + msg);
    }

    /*******************************************************************
     * FUNCTION SLOT
     ******************************************************************/
    log_info(msg) {
        console.log("- INFO - " + msg);
    }

    /*******************************************************************
     * FUNCTION SLOT
     ******************************************************************/
    log_debug(msg) {
        console.log("- DEBUG - " + msg);
    }
    /*******************************************************************
     * FUNCTION SLOT
     ******************************************************************/
    log_stack(stack) {
        console.log(stack)
    }

    /*******************************************************************
     * FUNCTION
     ******************************************************************/
    is_connected() {
        return connected;
    }

    /*******************************************************************
     * FUNCTION SLOT
     ******************************************************************/
    add_graph(name, graph) {
        Logger.log_debug("Add Graph: Name = " + name)

        var settings;

        for (let i = 0; i < DEMO_LINE_CONFIG.length; i++) {
            let s = DEMO_LINE_CONFIG[i]
            if (s["name"] === name) {
                settings = s;
                break;
            }
        }

        signal_list[name] = { "graph": graph, type: settings["type"] };
    }


    set_plot_area(area) {
        plot_area = area;
    }

    set_axis(x_axis, y_axis) {
        xAxis = x_axis;
        yAxis = y_axis;
    }

    ui_setup_status(status) {
        ui_setup_done = status
    }

}
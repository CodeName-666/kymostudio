import QtQuick 6.4
import Common 1.0
import Backend 1.0
import KymoUi 1.0
import "Workspace"


AppUi {
    id: appRoot
    objectName: "appRoot"

    workspaceController: WorkspaceController {
        id: workspace
        objectName: "workspaceController"
    }


    Component.onCompleted: {
        Logger.log_info("App: Component.onCompleted - Initializing application")
        appController = App.create()

        if(typeof Backend === 'undefined')
        {
            Logger.log_error("App: Python Backend is not available - start the app via run.py");
            return
        }
        appController.setup(appRoot, Backend);
        workspaceController.initialize(appController, Backend)
        connectSignals();
        initializeWorkbench();

        Logger.log_info("App: Initialization completed");
    }

    Component.onDestruction: {
        Logger.log_info("App: Component.onDestruction - Cleaning up")
        disconnectSignals()
        workspaceController.shutdown()
        Logger.log_info("App: Cleanup completed")
    }


    function connectSignals() {
        if (Validators.isValid(appController) && Validators.isValidFunction(appController.events)) {
            var events = appController.events()
            if (Validators.isValid(events) && Validators.isValid(events.status_message)) {
                events.status_message.connect(showStatusMessage)
            }
        }
    }

    function disconnectSignals() {
        if (Validators.isValid(appController) && Validators.isValidFunction(appController.events)) {
            var events = appController.events()
            if (Validators.isValid(events) && Validators.isValid(events.status_message)) {
                try { events.status_message.disconnect(showStatusMessage) } catch (e) {}
            }
        }
    }

}

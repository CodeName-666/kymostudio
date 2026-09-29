.pragma library


const ERROR = 40
const WARNING = 30
const INFO = 20
const DEBUG = 10
const NOTSET = 0

var levelToName = {
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
}

var nameToLevel = {
    'ERROR': ERROR,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}

var interface = undefined;
var stack_logging_enabled;
var logging_level;

/*******************************************************************
 * INTERNAL FUNCTION
 ******************************************************************/
function setup(logger_interface, stack_logging = true, logger_level = NOTSET) {
    interface = logger_interface
    stack_logging_enabled = stack_logging
    logging_level = logger_level
}


/*******************************************************************
 * FUNCTION SLOT
 ******************************************************************/
function log_error(msg, caller = undefined) {
    log_messages('ERROR',msg, caller);
}

/*******************************************************************
 * FUNCTION SLOT
 ******************************************************************/
function log_warning(msg, caller = undefined) {
    log_messages('WARNING',msg, caller);
}

/*******************************************************************
 * FUNCTION SLOT
 ******************************************************************/
function log_info(msg, caller = undefined) {
    log_messages('INFO',msg, caller);
}

/*******************************************************************
 * FUNCTION SLOT
 ******************************************************************/
function log_debug(msg, caller = undefined) {

    log_messages('DEBUG',msg, caller);
}


function log_internal(type, msg) {
    console.log("INTERNAL LOG: " + type + " - " + msg);
}




function log_messages(type, msg, caller = undefined )
{

    var fnc_name
    if(caller !== undefined)
    {
        fnc_name = caller.name
    }

    if(interface !== undefined)
    {
        switch(type) {
            case 'ERROR':
                interface.log_error(msg);
            break;
            case 'WARNING':
                interface.log_warning(msg);
            break;
            case 'INFO':
                interface.log_info(msg);
            break;
            case 'DEBUG':
                interface.log_debug(msg);
            break;
        }
    } else {
        log_internal(type,msg);
    }

    if(stack_logging_enabled) {
        var e = new Error()
        interface.log_stack(e.stack)
    }
}

function loglevel_to_name(level) {
    return levelToName[level];
}


function logname_to_level(name) {
    return nameToLevel[name];
}

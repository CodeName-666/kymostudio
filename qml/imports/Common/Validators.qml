pragma Singleton
import QtQuick 6.4

QtObject {
    // Consistent null/undefined checking
    function isValid(value) {
        return value !== null && value !== undefined
    }

    function isValidString(value) {
        return isValid(value) && value !== ""
    }

    function isValidObject(obj) {
        return isValid(obj) && typeof obj === "object"
    }

    function isValidFunction(fn) {
        return isValid(fn) && typeof fn === "function"
    }

    // Safe property access
    function getProperty(obj, propName, defaultValue) {
        if(!isValid(obj)) {
            return defaultValue !== undefined ? defaultValue : null
        }
        var value = obj[propName]
        return isValid(value) ? value : (defaultValue !== undefined ? defaultValue : null)
    }

    // Network validation
    function isValidPort(port) {
        var portNum = parseInt(port)
        return !isNaN(portNum) && portNum >= 1 && portNum <= 65535
    }

    function isValidIPv4(ip) {
        if(!isValidString(ip)) return false

        var parts = ip.split(".")
        if(parts.length !== 4) return false

        for(var i = 0; i < parts.length; i++) {
            var num = parseInt(parts[i])
            if(isNaN(num) || num < 0 || num > 255) {
                return false
            }
        }
        return true
    }

    function isValidHostname(hostname) {
        if(!isValidString(hostname)) return false

        // Allow localhost
        if(hostname === "localhost") return true

        // Basic hostname validation (alphanumeric, dots, hyphens)
        var hostnameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
        return hostnameRegex.test(hostname)
    }

    function isValidHost(host) {
        return isValidIPv4(host) || isValidHostname(host)
    }

    // MQTT Topic validation
    function isValidMQTTTopic(topic) {
        if(!isValidString(topic)) return false

        // MQTT topics should not contain null character, and # or + have special meaning
        // Basic validation: non-empty, no null chars
        return topic.length > 0 && topic.indexOf('\0') === -1
    }
}

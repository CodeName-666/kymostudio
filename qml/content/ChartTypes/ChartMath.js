.pragma library

/** A finite, non-degenerate range, including constant signals and zero. */
function paddedRange(low, high, fraction) {
    if (!isFinite(low) || !isFinite(high) || low > high) return [0, 1]
    var f = fraction === undefined ? 0.05 : fraction
    var magnitude = Math.max(Math.abs(low), Math.abs(high), 1e-9)
    var spread = high / magnitude - low / magnitude
    var pad = magnitude * Math.max(spread * f, spread === 0 ? 0.05 : 1e-12)
    var minimum = low - pad
    var maximum = high + pad
    if (!isFinite(minimum)) minimum = -Number.MAX_VALUE
    if (!isFinite(maximum)) maximum = Number.MAX_VALUE
    return [minimum, maximum]
}

/** Zoom an axis around a point expressed as a fraction of its visible span. */
function zoomRange(low, high, factor, anchorRatio) {
    var anchor = low + (high - low) * anchorRatio
    var span = (high - low) * factor
    return [anchor - span * anchorRatio, anchor + span * (1 - anchorRatio)]
}

/** Keep exactly the newest limit entries without copying a huge backlog. */
function tail(existing, incoming, limit) {
    if (incoming.length >= limit) return incoming.slice(incoming.length - limit)
    return existing.slice(Math.max(0, existing.length + incoming.length - limit)).concat(incoming)
}

/** Qt's native list append avoids one Python/QML boundary per sample. */
function appendBatch(series, points, limit, bridge) {
    limit = Math.max(1, Math.floor(limit))
    var clean = []
    for (var i = Math.max(0, points.length - limit); i < points.length; i++) {
        var p = points[i]
        if (p && typeof p[0] === 'number' && typeof p[1] === 'number' && isFinite(p[0]) && isFinite(p[1]))
            clean.push([p[0], p[1]])
    }
    if (bridge) return bridge.appendBatch(series, clean, limit)
    // Designer/simulator fallback; the Python application uses the native path.
    var excess = Math.min(series.count, Math.max(0, series.count + clean.length - limit))
    if (excess) series.removePoints(0, excess)
    for (var k = 0; k < clean.length; k++) series.append(clean[k][0], clean[k][1])
    return series.count
}

"""Validation of saved layout/assignment metadata, independent of QML."""
import math
from copy import deepcopy

CHART_TYPES = {'time_series', 'xy_line', 'xy_scatter', 'xyz_scatter'}


def validate_workspace(value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError('Workspace must be an object')
    if not value:
        return {}
    if type(value.get('version')) is not int or value['version'] != 1:
        raise ValueError('Unsupported workspace version')
    charts = value.get('charts', [])
    signals = value.get('signals', [])
    assignments = value.get('assignments', [])
    if not isinstance(charts, list) or len(charts) > 16:
        raise ValueError('Workspace supports at most 16 charts')
    if not isinstance(signals, list) or len(signals) > 256:
        raise ValueError('Workspace supports at most 256 signals')
    if not isinstance(assignments, list) or len(assignments) > 1024:
        raise ValueError('Too many curve assignments')
    ids, signal_ids = set(), set()
    for chart in charts:
        if not isinstance(chart, dict) or chart.get('chartType') not in CHART_TYPES:
            raise ValueError('Unknown chart type')
        key = chart.get('chartId')
        if not isinstance(key, str) or not key or len(key) > 200 or key in ids:
            raise ValueError('Chart IDs must be unique nonempty strings')
        if not isinstance(chart.get('chartTitle'), str) or len(chart['chartTitle']) > 200:
            raise ValueError('Invalid chart title')
        for field in ('xPos', 'yPos', 'windowWidth', 'windowHeight'):
            n = chart.get(field, 0 if field.endswith('Pos') else 600)
            if type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 10000:
                raise ValueError('Invalid window geometry')
            if field in ('windowWidth', 'windowHeight') and n < 100:
                raise ValueError('Chart window too small')
        for field in ('maximized', 'minimized'):
            if field in chart and type(chart[field]) is not bool:
                raise ValueError('Window state must be boolean')
        if 'view' in chart:
            view = chart['view']
            if not isinstance(view, dict):
                raise ValueError('Axis state must be an object')
            for axis in ('xMin', 'xMax', 'yMin', 'yMax'):
                number = view.get(axis)
                if type(number) not in (int, float):
                    raise ValueError('Axis limits must be finite numbers')
                try:
                    finite = math.isfinite(number)
                except OverflowError:
                    finite = False
                if not finite:
                    raise ValueError('Axis limits must be finite numbers')
            if view['xMin'] >= view['xMax'] or view['yMin'] >= view['yMax']:
                raise ValueError('Axis minimum must be smaller than its maximum')
            if 'timeWindow' in view:
                window = view['timeWindow']
                if type(window) not in (int, float) or not 1 <= window <= 86400:
                    raise ValueError('Time window must be 1–86400 seconds')
            for flag in ('autoScroll', 'autoScaleY'):
                if flag in view and type(view[flag]) is not bool:
                    raise ValueError('Automatic axis state must be boolean')
        ids.add(key)
    for signal in signals:
        if not isinstance(signal, dict):
            raise ValueError('Invalid signal metadata')
        for field in ('uniqueId', 'displayName', 'color', 'interfaceType'):
            if not isinstance(signal.get(field), str) or len(signal[field]) > 300:
                raise ValueError('Invalid signal field: ' + field)
        if not signal['uniqueId'] or signal['uniqueId'] in signal_ids:
            raise ValueError('Signal IDs must be unique')
        if type(signal.get('dataId')) is not int or not 0 <= signal['dataId'] <= 255:
            raise ValueError('Invalid signal data ID')
        signal_ids.add(signal['uniqueId'])
    keys = set()
    per_chart: dict[str, int] = {}
    for line in assignments:
        if not isinstance(line, dict) or line.get('chartId') not in ids or line.get('uniqueId') not in signal_ids:
            raise ValueError('Assignment points to a missing chart or signal')
        if line.get('valueField') not in (None, '', 'x', 'y'):
            raise ValueError('Unknown value field')
        if 'visible' in line and type(line['visible']) is not bool:
            raise ValueError('Visibility must be boolean')
        key = (line['chartId'], line['uniqueId'], line.get('valueField'))
        if key in keys:
            raise ValueError('Duplicate assignment')
        keys.add(key)
        per_chart[line['chartId']] = per_chart.get(line['chartId'], 0) + 1
        if per_chart[line['chartId']] > 64:
            raise ValueError('At most 64 curves per chart')
    result = deepcopy(value)
    result.setdefault('charts', [])
    result.setdefault('signals', [])
    result.setdefault('assignments', [])
    return result

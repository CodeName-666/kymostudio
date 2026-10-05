"""Saved layout is untrusted input and must never feed invalid axes into Qt."""
from copy import deepcopy
import pytest
from Core.workspace import validate_workspace

CHART = {'chartId': 'one', 'chartType': 'time_series', 'chartTitle': 'Signal',
         'xPos': 0, 'yPos': 0, 'windowWidth': 600, 'windowHeight': 400}
VIEW = {'xMin': 0, 'xMax': 60, 'yMin': -1, 'yMax': 1, 'timeWindow': 60,
        'autoScroll': True, 'autoScaleY': True}

def document(view=None):
    chart = deepcopy(CHART)
    if view is not None:
        chart['view'] = view
    return {'version': 1, 'charts': [chart], 'signals': [], 'assignments': []}

@pytest.mark.parametrize('field,value', [
    ('xMin', float('nan')), ('xMax', float('inf')), ('yMin', True),
    ('yMax', '2'), ('timeWindow', 0), ('timeWindow', 90000),
    ('autoScroll', 'false'), ('autoScaleY', 1),
    ('xMin', 60), ('yMin', 2),
])
def test_invalid_saved_axis_values_are_rejected(field, value):
    with pytest.raises(ValueError):
        validate_workspace(document({**VIEW, field: value}))

@pytest.mark.parametrize('view', [[], 'bad', {'xMin': 0}])
def test_axis_state_must_be_a_complete_object(view):
    with pytest.raises(ValueError):
        validate_workspace(document(view))

def test_version_boolean_is_not_a_schema_version():
    with pytest.raises(ValueError):
        validate_workspace({**document(), 'version': True})

def test_valid_workspace_is_copy_isolated_and_normalizes_missing_arrays():
    data = {'version': 1, 'charts': [CHART]}
    restored = validate_workspace(data)
    assert restored['signals'] == []
    assert restored['assignments'] == []
    restored['charts'][0]['chartTitle'] = 'changed'
    assert data['charts'][0]['chartTitle'] == 'Signal'

def test_valid_view_and_empty_layout_are_supported():
    assert validate_workspace(document(VIEW)) == document(VIEW)
    assert validate_workspace({}) == {}

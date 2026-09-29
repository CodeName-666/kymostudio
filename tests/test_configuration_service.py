import json
from pathlib import Path
import pytest
from Core.configuration import atomic_json_write, validate_configuration, local_path, ConfigurationRepository

GOOD = {'interfaces': [{'type':'Test', 'default': {'sample_ms':50}}], 'qml': {'interfaces':['Test']}}

@pytest.mark.parametrize('data', [None, [], {}, {'interfaces':[]}, {'interfaces':[{'type':'Test'}, {'type':'Test'}]},
    {**GOOD, 'saved_connections':[{'id':'a','type':'Unknown','name':'A','settings':{}}]},
    {**GOOD, 'saved_connections':[{'id':'a','type':'Test','name':'A','settings':[], 'created_at':1}]},
    {**GOOD, 'interfaces':[{'type':'Test','default':{'sample_ms':float('nan')}}]},
])
def test_invalid_configs_are_rejected(data):
    with pytest.raises(ValueError): validate_configuration(data)


def test_failed_write_preserves_existing_json_and_removes_temp_files(tmp_path):
    target = tmp_path/'config.json'
    atomic_json_write(target, GOOD)
    before = target.read_bytes()
    with pytest.raises(ValueError): atomic_json_write(target, {'x':float('nan')})
    assert target.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ['config.json']


def test_repository_uses_copy_and_returns_copies(tmp_path):
    repo = ConfigurationRepository(tmp_path/'private'/'config.json', GOOD)
    a = repo.load(); a['interfaces'][0]['default']['sample_ms']=1
    assert repo.load()['interfaces'][0]['default']['sample_ms']==50
    repo.save(GOOD)
    assert (tmp_path/'private'/'config.json').is_file()


def test_file_url_spaces_and_localhost(tmp_path):
    p = tmp_path/'a b.json'
    assert local_path(p.as_uri()) == p
    assert local_path('file://localhost'+str(p).replace(' ','%20')) == p
    assert local_path(str(tmp_path/'literal%20.json')).name == 'literal%20.json'

@pytest.mark.parametrize('path', ['', 'https://example.com/x', 'file:///tmp/a?x=1'])
def test_no_remote_urls_or_query_strings(path):
    with pytest.raises(ValueError): local_path(path)

@pytest.mark.parametrize('settings', [
    {'frame_interval_ms':'fast'}, {'frame_interval_ms':True}, {'frame_interval_ms':0},
    {'display_points_per_signal':1000000}, {'downsample_enabled':'false'}, {'downsample_target_hz':0},
])
def test_invalid_performance_values_do_not_reach_qt(settings):
    with pytest.raises(ValueError): validate_configuration({**GOOD,'performance':settings})

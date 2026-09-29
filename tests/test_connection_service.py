"""Lifecycle tests use an injected in-memory transport, not a simulated Qt GUI."""
import pytest
from Backend.connection_service import ConnectionService

class Event:
    def __init__(self): self.callbacks=[]
    def connect(self, f): self.callbacks.append(f)
    def emit(self, *args):
        for f in self.callbacks: f(*args)

class Transport:
    def __init__(self, config):
        self.settings=dict(config); self.new_data=Event(); self.connection_changed=Event()
        self.active=False; self.starts=0; self.stops=0; self.fail_stop=False
    def config(self, settings): self.settings=dict(settings)
    def settings_valid(self): return self.settings.get('valid',True)
    def start(self):
        self.starts+=1; self.active=self.settings.get('ready',True)
        self.connection_changed.emit(self.active)
    def stop(self):
        self.stops+=1
        if self.fail_stop: raise TimeoutError('still running')
        self.active=False; self.connection_changed.emit(False)
    def is_connected(self): return self.active
    def deleteLater(self): pass

class Registry:
    def create_receiver(self, config): return Transport(config['default'])

@pytest.fixture
def service():
    return ConnectionService(Registry(), lambda *a:None, lambda:None, lambda *a:None, lambda *a:None)

def test_create_copies_settings_and_routes_payload(service):
    packets=[]; service.on_data=lambda *args: packets.append(args)
    settings={'ready':True}; key=service.create('Test','A', settings)
    settings['ready']=False
    info=service.connections[key]
    assert info.settings['ready'] is True
    info.receiver.new_data.emit(b'42')
    assert packets==[(key,b'42')]

def test_async_start_stays_connecting_until_confirmed(service):
    key=service.create('MQTT','A',{'ready':False})
    assert service.start(key)
    assert service.connections[key].status=='connecting'
    service.connections[key].receiver.connection_changed.emit(True)
    assert service.connections[key].status=='connected'

def test_update_active_connection_restarts_new_transport(service):
    key=service.create('Test','A',{'ready':True}); service.start(key)
    old=service.connections[key].receiver
    assert service.update_settings(key,{'ready':True,'rate':10})
    assert old.stops==1
    assert service.connections[key].receiver is not old
    assert service.connections[key].receiver.starts==1
    assert service.connections[key].status=='connected'

def test_invalid_update_preserves_existing_connection(service):
    key=service.create('Test','A',{'ready':True}); service.start(key)
    old=service.connections[key].receiver
    assert not service.update_settings(key,{'valid':False})
    assert service.connections[key].receiver is old
    assert old.active

def test_stop_failure_is_not_reported_as_disconnected(service):
    key=service.create('Test','A',{}); service.start(key)
    service.connections[key].receiver.fail_stop=True
    assert not service.stop(key)
    assert service.connections[key].status=='error'
    assert not service.shutdown()

def test_restore_does_not_autoconnect_and_rejects_duplicates(service):
    row={'id':'test_1','type':'Test','name':'A','settings':{}}
    assert service.restore(row)
    assert not service.restore(row)
    assert service.connections['test_1'].receiver.starts==0
    assert service.connections['test_1'].status=='disconnected'

def test_old_receiver_events_cannot_corrupt_replacement(service):
    packets=[]; service.on_data=lambda *a:packets.append(a)
    key=service.create('Test','A',{}); service.start(key)
    old=service.connections[key].receiver
    assert service.update_settings(key,{})
    old.connection_changed.emit(False)
    old.new_data.emit(b'old')
    assert service.connections[key].status=='connected'
    assert packets==[]

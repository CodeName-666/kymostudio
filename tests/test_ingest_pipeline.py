"""Worker-side parsing, batched hand-off and the single-replace chart bridge."""
import pytest
pytest.importorskip("PySide6", reason="Real Qt integration requires requirements-dev.txt")
from unittest.mock import Mock

from PySide6.QtCharts import QLineSeries
from PySide6.QtCore import QCoreApplication

from Backend.backend import Backend
from Backend.series_bridge import SeriesBridge
from Core.ingress import IngressQueue
from Receiver.binary_protocol import ProtocolError, encode_data_point
from Receiver.message import PlotDataPoint
from Receiver.receiver import Receiver
from Receiver.receiver_thread import ReceiverThread


class _Receiver(Receiver):
    def config(self, config): pass
    def settings_valid(self): return True
    def open_connection(self): return True
    def close_connection(self): pass
    def is_connected(self): return True


@pytest.fixture
def app():
    return QCoreApplication.instance() or QCoreApplication([])


@pytest.fixture
def backend(app):
    Backend._Backend__backend_instance = None
    instance = Backend()
    instance._save_connections_to_config = Mock()
    yield instance
    instance._batch_timer.stop()
    instance._Backend__com_updater_timer.stop()
    Backend._Backend__backend_instance = None


def test_put_many_keeps_newest_and_counts_oversized(app):
    queue = IngressQueue(capacity=2, max_payload_bytes=4)
    assert queue.put_many([("a", 1), ("big", 5), ("b", 1), ("c", 1)]) == 3
    assert queue.dropped == 2
    assert queue.drain(9) == ["b", "c"]


def test_worker_parses_and_hands_over_one_batch_per_tick(app):
    receiver, worker = _Receiver(), ReceiverThread()
    receiver.attach_thread(worker)
    batches = []
    receiver.samples_ready.connect(batches.append)
    worker.publish([encode_data_point(PlotDataPoint(id=5, value=2.5)), b"not a measurement"])
    receiver._drain_ingress()
    (batch,) = batches
    (point, rx_wall, rx_monotonic), error = batch
    assert (point.id, point.value) == (5, 2.5) and rx_wall > 0 and rx_monotonic > 0
    assert isinstance(error, ProtocolError)
    receiver.detach_thread()


def test_batch_ingest_keeps_arrival_order_and_reports_errors(backend):
    backend._queue_event = Mock()
    items = [(PlotDataPoint(id=i % 2, value=float(i)), 100.0 + i, 50.0 + i) for i in range(4)]
    backend._on_receiver_samples("Serial", items[:2] + [ProtocolError("bad")] + items[2:])
    assert [key for key, _ in backend._sample_store.snapshot()] == ["Serial_0", "Serial_1", "Serial_0", "Serial_1"]
    assert [s.y for s in backend._sample_store.samples("Serial_0")] == [0.0, 2.0]
    assert backend._received_total == 4 and backend._invalid_total == 1
    assert [p[1] for p in backend._frames_2d.queues["Serial_1"]] == [1.0, 3.0]
    assert backend._graph_state["Serial_0"]["color"].startswith("#")


def test_bridge_replaces_once_and_resyncs_after_external_clear(app):
    bridge, series = SeriesBridge(), QLineSeries()
    assert bridge.appendBatch(series, [[i, i] for i in range(5)], 3) == 3
    series.clear()
    assert bridge.appendBatch(series, [[9, 9]], 3) == 1
    assert series.at(0).x() == 9

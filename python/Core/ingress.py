"""Bounded thread-safe handoff; no Qt event or widget access in producers."""
from collections import deque
from threading import Lock


class IngressQueue:
    """Drop oldest on overload, never hide that loss from diagnostics.

    Capacity is per connection. The additional byte ceiling prevents a small
    number of unusually large packets from defeating the item-count bound.
    """

    def __init__(self, capacity: int = 2048, max_payload_bytes: int = 65536,
                 max_bytes: int = 4 * 1024 * 1024) -> None:
        if min(capacity, max_payload_bytes, max_bytes) < 1:
            raise ValueError("Queue limits must be positive")
        self._items: deque[bytes] = deque()
        self._lock = Lock()
        self._capacity = capacity
        self._max_payload = max_payload_bytes
        self._max_bytes = max_bytes
        self._bytes = 0
        self._dropped = 0

    @property
    def dropped(self) -> int:
        with self._lock:
            return self._dropped

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

    def put(self, payload: bytes) -> bool:
        with self._lock:
            if len(payload) > min(self._max_payload, self._max_bytes):
                self._dropped += 1
                return False
            while self._items and (len(self._items) >= self._capacity or
                                   self._bytes + len(payload) > self._max_bytes):
                self._bytes -= len(self._items.popleft())
                self._dropped += 1
            self._items.append(bytes(payload))
            self._bytes += len(payload)
            return True

    def drain(self, maximum: int = 256) -> list[bytes]:
        with self._lock:
            result = [self._items.popleft() for _ in range(min(maximum, len(self._items)))]
            self._bytes -= sum(map(len, result))
            return result

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._bytes = 0

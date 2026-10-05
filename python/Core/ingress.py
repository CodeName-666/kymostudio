# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Bounded thread-safe handoff; no Qt event or widget access in producers.

Items are opaque (raw payloads or already parsed samples); ``size`` is the
wire size used for the memory bound and defaults to ``len(item)``.
"""
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
        self._items: deque = deque()
        self._sizes: deque[int] = deque()
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

    @property
    def capacity(self) -> int:
        return self._capacity

    def put(self, item, size: int | None = None) -> bool:
        size = len(item) if size is None else size
        with self._lock:
            if size > min(self._max_payload, self._max_bytes):
                self._dropped += 1
                return False
            while self._items and (len(self._items) >= self._capacity or
                                   self._bytes + size > self._max_bytes):
                self._items.popleft()
                self._bytes -= self._sizes.popleft()
                self._dropped += 1
            self._items.append(bytes(item) if isinstance(item, (bytearray, memoryview)) else item)
            self._sizes.append(size)
            self._bytes += size
            return True

    def put_many(self, entries) -> int:
        """put() for many (item, size) pairs under a single lock; returns accepted count."""
        accepted = 0
        with self._lock:
            limit = min(self._max_payload, self._max_bytes)
            items, sizes = self._items, self._sizes
            for item, size in entries:
                if size > limit:
                    self._dropped += 1
                    continue
                while items and (len(items) >= self._capacity or self._bytes + size > self._max_bytes):
                    items.popleft()
                    self._bytes -= sizes.popleft()
                    self._dropped += 1
                items.append(item)
                sizes.append(size)
                self._bytes += size
                accepted += 1
        return accepted

    def drain(self, maximum: int = 256) -> list:
        with self._lock:
            count = min(maximum, len(self._items))
            result = [self._items.popleft() for _ in range(count)]
            self._bytes -= sum(self._sizes.popleft() for _ in range(count))
            return result

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._sizes.clear()
            self._bytes = 0

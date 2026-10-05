# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Real queue behavior, including concurrent producers and memory limits."""
from concurrent.futures import ThreadPoolExecutor
from Core.ingress import IngressQueue


def test_keeps_newest_with_explicit_loss_count():
    queue = IngressQueue(capacity=3)
    for i in range(10):
        queue.put(str(i).encode())
    assert queue.dropped == 7
    assert queue.drain(2) == [b'7', b'8']
    assert queue.drain(9) == [b'9']


def test_concurrent_producers_never_exceed_capacity():
    queue = IngressQueue(capacity=100)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: [queue.put(b'x') for _ in range(1000)], range(4)))
    assert len(queue) == 100
    assert queue.dropped == 3900


def test_oversized_payload_cannot_bypass_memory_limit():
    queue = IngressQueue(capacity=3, max_payload_bytes=4)
    assert not queue.put(b'12345')
    assert queue.dropped == 1
    assert queue.put(b'1234')
    queue.clear()
    assert len(queue) == 0

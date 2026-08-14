from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Iterable, Protocol
from uuid import uuid4

from fastapi.encoders import jsonable_encoder


def event_envelope(event: str, data: dict) -> dict:
    return {
        "event": event,
        "event_id": f"evt_{uuid4().hex}",
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": jsonable_encoder(data),
    }


class EventBroker(Protocol):
    def publish(self, topics: Iterable[str], event: str, data: dict) -> None: ...

    def subscribe(self, topic: str) -> "EventSubscription": ...

    def unsubscribe(self, subscription: "EventSubscription") -> None: ...


@dataclass(frozen=True, slots=True)
class EventSubscription:
    id: str
    topic: str
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue[dict]


class InMemoryEventBroker:
    """단일 프로세스용 브로커. EventBroker 계약을 유지해 Redis 구현으로 교체할 수 있다."""

    def __init__(self, queue_size: int = 100) -> None:
        self.queue_size = queue_size
        self._subscriptions: dict[str, dict[str, EventSubscription]] = {}
        self._lock = Lock()

    def subscribe(self, topic: str) -> EventSubscription:
        subscription = EventSubscription(
            id=str(uuid4()),
            topic=topic,
            loop=asyncio.get_running_loop(),
            queue=asyncio.Queue(maxsize=self.queue_size),
        )
        with self._lock:
            self._subscriptions.setdefault(topic, {})[subscription.id] = subscription
        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        with self._lock:
            topic_subscriptions = self._subscriptions.get(subscription.topic)
            if topic_subscriptions is None:
                return
            topic_subscriptions.pop(subscription.id, None)
            if not topic_subscriptions:
                self._subscriptions.pop(subscription.topic, None)

    def publish(self, topics: Iterable[str], event: str, data: dict) -> None:
        envelope = event_envelope(event, data)
        with self._lock:
            subscriptions = [
                subscription
                for topic in set(topics)
                for subscription in self._subscriptions.get(topic, {}).values()
            ]
        for subscription in subscriptions:
            try:
                subscription.loop.call_soon_threadsafe(self._enqueue, subscription.queue, envelope)
            except RuntimeError:
                self.unsubscribe(subscription)

    @staticmethod
    def _enqueue(queue: asyncio.Queue[dict], envelope: dict) -> None:
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(envelope)

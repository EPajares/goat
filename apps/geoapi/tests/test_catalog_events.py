"""Catalog change events: write-bump + Redis pub/sub (fakes, no Redis)."""

import time
from typing import Any

import pytest

from geoapi import catalog_events


class FakePubSub:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self.subscribed: list[str] = []

    def subscribe(self, channel: str) -> None:
        self.subscribed.append(channel)

    def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 1.0):
        if self.messages:
            return self.messages.pop(0)
        time.sleep(0.01)
        return None

    def close(self) -> None:
        pass


class FakeRedis:
    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []
        self._pubsub = FakePubSub()

    def publish(self, channel: str, message: str) -> None:
        self.published.append((channel, message))

    def pubsub(self) -> FakePubSub:
        return self._pubsub


@pytest.fixture()
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    r = FakeRedis()
    monkeypatch.setattr(catalog_events, "get_redis_client", lambda: r)
    return r


@pytest.fixture()
def refresh_spy(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    calls = {"n": 0}

    def spy() -> None:
        calls["n"] += 1

    monkeypatch.setattr(catalog_events, "refresh_local_pins", spy)
    return calls


def test_notify_publishes_and_refreshes(fake_redis: FakeRedis, refresh_spy) -> None:
    catalog_events.notify_catalog_changed()
    deadline = time.monotonic() + 2.0
    while refresh_spy["n"] == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert refresh_spy["n"] == 1
    assert fake_redis.published == [
        (catalog_events.CHANNEL, catalog_events.INSTANCE_ID)
    ]


def test_notify_survives_redis_down(monkeypatch, refresh_spy) -> None:
    monkeypatch.setattr(catalog_events, "get_redis_client", lambda: None)
    catalog_events.notify_catalog_changed()  # must not raise
    deadline = time.monotonic() + 2.0
    while refresh_spy["n"] == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert refresh_spy["n"] == 1


def test_subscriber_skips_own_messages(fake_redis: FakeRedis, refresh_spy) -> None:
    fake_redis._pubsub.messages = [
        {"type": "message", "data": catalog_events.INSTANCE_ID.encode()},
        {"type": "message", "data": b"other-pod"},
    ]
    catalog_events.start_subscriber()
    try:
        deadline = time.monotonic() + 2.0
        while refresh_spy["n"] == 0 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert refresh_spy["n"] == 1  # only the foreign message triggered
    finally:
        catalog_events.stop_subscriber()

"""Cross-pod DuckLake catalog-change notifications.

A pod that commits a write bumps its own snapshot pins immediately and
publishes a best-effort Redis message so other pods refresh within ~100 ms
instead of waiting for the next poll tick. The poll remains the correctness
backbone: Redis being down only widens edit-visibility back to the refresh
interval.
"""

import logging
import threading
import uuid

from geoapi.tile_cache import get_redis_client

logger = logging.getLogger(__name__)

CHANNEL = "ducklake:changed"
INSTANCE_ID = uuid.uuid4().hex

_subscriber_thread: threading.Thread | None = None
_subscriber_stop = threading.Event()


def refresh_local_pins() -> None:
    """Force-refresh all pinned readers in this process (rate-limited by pins).

    Synchronous (~1s when a rebuild is needed) — callers on the event loop
    should wrap it in ``asyncio.to_thread``.
    """
    from geoapi.ducklake import ducklake_manager
    from geoapi.ducklake_pool import ducklake_pool

    ducklake_pool.force_pin_refresh()
    ducklake_manager.force_pin_refresh()


def notify_catalog_changed() -> None:
    """Called after a successful local write: bump pins, tell other pods.

    Fire-and-forget: the rebuild (~1 s) runs on a background thread so the
    write response is not delayed, and the publish swallows Redis failures.
    """
    threading.Thread(
        target=refresh_local_pins, daemon=True, name="pin-write-bump"
    ).start()
    try:
        client = get_redis_client()
        if client is not None:
            client.publish(CHANNEL, INSTANCE_ID)
    except Exception as e:
        logger.debug("Catalog-change publish skipped: %s", e)


def _subscriber_loop() -> None:
    pubsub = None
    while not _subscriber_stop.is_set():
        try:
            if pubsub is None:
                client = get_redis_client()
                if client is None:
                    _subscriber_stop.wait(5.0)
                    continue
                pubsub = client.pubsub()  # type: ignore[no-untyped-call]
                pubsub.subscribe(CHANNEL)
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None or message.get("type") != "message":
                continue
            data = message.get("data")
            sender = data.decode() if isinstance(data, bytes) else str(data)
            if sender == INSTANCE_ID:
                continue
            refresh_local_pins()
        except Exception as e:
            logger.debug("Catalog-change subscriber reset: %s", e)
            if pubsub is not None:
                try:
                    pubsub.close()
                except Exception:
                    pass
                pubsub = None
            _subscriber_stop.wait(5.0)
    if pubsub is not None:
        try:
            pubsub.close()
        except Exception:
            pass


def start_subscriber() -> None:
    """Start the background subscriber (idempotent)."""
    global _subscriber_thread
    if _subscriber_thread is not None and _subscriber_thread.is_alive():
        return
    _subscriber_stop.clear()
    _subscriber_thread = threading.Thread(
        target=_subscriber_loop, daemon=True, name="ducklake-catalog-events"
    )
    _subscriber_thread.start()


def stop_subscriber() -> None:
    """Stop the background subscriber."""
    _subscriber_stop.set()
    if _subscriber_thread is not None:
        _subscriber_thread.join(timeout=3.0)

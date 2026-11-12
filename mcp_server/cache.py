"""Cache TTL đơn giản trong bộ nhớ (design 4.3: cache list_members, list_sprints)."""

import time
from collections.abc import Callable, Hashable
from typing import Any

DEFAULT_TTL_SECONDS = 300.0


class TTLCache:
    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._items: dict[Hashable, tuple[float, Any]] = {}

    def get(self, key: Hashable) -> Any | None:
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self._clock() >= expires_at:
            del self._items[key]
            return None
        return value

    def set(self, key: Hashable, value: Any) -> None:
        self._items[key] = (self._clock() + self._ttl, value)

    def clear(self) -> None:
        self._items.clear()

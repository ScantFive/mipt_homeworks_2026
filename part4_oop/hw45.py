from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from part4_oop.interfaces import Cache, HasCache, Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class DictStorage(Storage[K, V]):
    _data: dict[K, V] = field(default_factory=dict, init=False)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def exists(self, key: K) -> bool:
        return key in self._data

    def remove(self, key: K) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


@dataclass
class FIFOPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key not in self._order:
            self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._order) > 0


@dataclass
class LRUPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._order) > 0


@dataclass
class LFUPolicy(Policy[K]):
    capacity: int = 5
    _last_key: K | None = None
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)

    def register_access(self, key: K) -> None:
        if key in self._key_counter:
            current_count = self._key_counter.get(key, 0)
            self._key_counter.update({key: current_count + 1})
            self._last_key = None
            return

        if len(self._key_counter) >= self.capacity and self._key_counter:
            self._last_key = min(self._key_counter, key=self._get_access)
        else:
            self._last_key = None

        self._key_counter[key] = 1

    def get_key_to_evict(self) -> K | None:
        if len(self._key_counter) < self.capacity:
            return None
        candidates = [k for k in self._key_counter if k != self._last_key]
        if not candidates:
            return self._last_key

        return min(candidates, key=lambda k: self._key_counter[k])

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)
        if key == self._last_key:
            self._last_key = None

    def clear(self) -> None:
        self._key_counter.clear()
        self._last_key = None

    @property
    def has_keys(self) -> bool:
        return len(self._key_counter) > 0

    def _candidate(self) -> K | None:
        if self._last_key not in self._key_counter:
            self._last_key = None
        return self._last_key

    def _get_access(self, key: K) -> int:
        return self._key_counter[key]



class MIPTCache(Cache[K, V]):
    def __init__(self, storage: Storage[K, V], policy: Policy[K]) -> None:
        self._storage = storage
        self._policy = policy

    def set(self, key: K, value: V) -> None:
        self._storage.set(key, value)
        self._policy.register_access(key)

        evict_key = self._policy.get_key_to_evict()
        if evict_key is not None and evict_key != key:
            self._storage.remove(evict_key)
            self._policy.remove_key(evict_key)

    def get(self, key: K) -> V | None:
        if self._storage.exists(key):
            self._policy.register_access(key)
            return self._storage.get(key)
        return None

    def exists(self, key: K) -> bool:
        return self._storage.exists(key)

    def remove(self, key: K) -> None:
        if self._storage.exists(key):
            self._storage.remove(key)
            self._policy.remove_key(key)

    def clear(self) -> None:
        self._storage.clear()
        self._policy.clear()


class CachedProperty[V]:
    def __init__(self, func: Callable[..., V]) -> None:
        self._func = func
        self._cache_key = func.__name__

    def __get__(self, instance: HasCache[Any, Any] | None, owner: type) -> V:
        if instance is None:
            return self

        cache = instance.cache
        if cache.exists(self._cache_key):
            return cache.get(self._cache_key)

        value = self._func(instance)
        cache.set(self._cache_key, value)
        return value

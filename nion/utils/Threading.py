import threading
from collections.abc import MutableMapping
from typing import TypeVar, Generic, Iterator, Optional, Tuple, List, Dict

K = TypeVar('K')
V = TypeVar('V')

class ThreadSafeDict(MutableMapping[K, V], Generic[K, V]):
    def __init__(self, *args, **kwargs) -> None:
        self.__data: Dict[K, V] = dict(*args, **kwargs)
        self.__lock = threading.RLock()

    # --- Core mapping methods ---
    def __getitem__(self, key: K) -> V:
        with self.__lock:
            return self.__data[key]

    def __setitem__(self, key: K, value: V) -> None:
        with self.__lock:
            self.__data[key] = value

    def __delitem__(self, key: K) -> None:
        with self.__lock:
            del self.__data[key]

    def __iter__(self) -> Iterator[K]:
        with self.__lock:
            return iter(list(self.__data))

    def __len__(self) -> int:
        with self.__lock:
            return len(self.__data)

    def __contains__(self, key: object) -> bool:
        with self.__lock:
            return key in self.__data

    # --- Optional helpers ---
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        with self.__lock:
            return self.__data.get(key, default)

    def setdefault(self, key: K, default: V) -> V:
        with self.__lock:
            return self.__data.setdefault(key, default)

    def pop(self, key: K, default: Optional[V] = None) -> Optional[V]:
        with self.__lock:
            return self.__data.pop(key, default)

    def popitem(self) -> Tuple[K, V]:
        with self.__lock:
            return self.__data.popitem()

    def update(self, *args, **kwargs) -> None:
        with self.__lock:
            self.__data.update(*args, **kwargs)

    def clear(self) -> None:
        with self.__lock:
            self.__data.clear()

    def keys(self) -> List[K]:
        with self.__lock:
            return list(self.__data.keys())

    def values(self) -> List[V]:
        with self.__lock:
            return list(self.__data.values())

    def items(self) -> List[Tuple[K, V]]:
        with self.__lock:
            return list(self.__data.items())

    def copy(self) -> 'ThreadSafeDict[K, V]':
        with self.__lock:
            return ThreadSafeDict(self.__data.copy())

    def to_dict(self) -> Dict[K, V]:
        with self.__lock:
            return dict(self.__data)

    def __repr__(self) -> str:
        with self.__lock:
            return f"{self.__class__.__name__}({self.__data!r})"

    # --- Optional: context manager for atomic operations ---
    def locked(self) -> threading.RLock:
        return self.__lock

import abc
import collections
import copy
import typing
import weakref

from . import Observable

from .ReferenceCounting import weak_partial


AccessorType = typing.Callable[[typing.Any], typing.Any]


class Accessor(abc.ABC):
    @abc.abstractmethod
    def get(self, o: Observable.Observable) -> typing.Any: ...


class DirectAccessor(Accessor):
    def __repr__(self) -> str:
        return f"self"

    def get(self, o: Observable.Observable) -> typing.Any:
        return o


class KeyAccessor(Accessor):
    def __init__(self, accessor: Accessor, key: str) -> None:
        self.accessor = accessor
        self.key = key

    def __repr__(self) -> str:
        return f"{self.accessor}.{self.key}"

    def get(self, o: Observable.Observable) -> typing.Any:
        return getattr(self.accessor.get(o), self.key)


class IndexAccessor(Accessor):
    def __init__(self, accessor: Accessor, index: int) -> None:
        self.accessor = accessor
        self.index = index

    def __repr__(self) -> str:
        return f"{self.accessor}[{self.index}]"

    def get(self, o: Observable.Observable) -> typing.Any:
        return self.accessor.get(o)[self.index]


class RecorderEntry(abc.ABC):
    @abc.abstractmethod
    def apply(self, o: Observable.Observable) -> None: ...


class KeyRecorderEntry(RecorderEntry):
    def __init__(self, accessor: Accessor, key: str, item: typing.Any) -> None:
        self.accessor = accessor
        self.key = key
        self.item = item

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.accessor}, {self.key}, {self.item})"

    def apply(self, o: Observable.Observable) -> None:
        setattr(self.accessor.get(o), self.key, self.item)


class InsertRecorderEntry(RecorderEntry):
    def __init__(self, accessor: Accessor, key: str, index: int, item: typing.Any) -> None:
        self.accessor = accessor
        self.key = key
        self.index = index
        self.item = item

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.accessor}, {self.key}, {self.index}, {self.item})"

    def apply(self, o: Observable.Observable) -> None:
        self.accessor.get(o).insert_item(self.key, self.index, self.item)


class RemoveRecorderEntry(RecorderEntry):
    def __init__(self, accessor: Accessor, key: str, index: int) -> None:
        self.accessor = accessor
        self.key = key
        self.index = index

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.accessor}, {self.key}, {self.index})"

    def apply(self, o: Observable.Observable) -> None:
        self.accessor.get(o).remove_item(self.key, getattr(self.accessor.get(o), self.key)[self.index])


class RecorderLogger:
    def __init__(self) -> None:
        self.__items: typing.List[RecorderEntry] = list()

    def append(self, recorder_entry: RecorderEntry) -> None:
        self.__items.append(recorder_entry)

    def apply(self, object: Observable.Observable) -> None:
        for logger_item in self.__items:
            logger_item.apply(object)


class RecorderDelegateProtocol(typing.Protocol):
    def property_changed(self, accessor: Accessor, key: str, value: typing.Any) -> None: ...
    def set_item(self, accessor: Accessor, key: str, item: typing.Any) -> None: ...
    def insert_item(self, accessor: Accessor, key: str, index: int, item: typing.Any) -> None: ...
    def remove_item(self, accessor: Accessor, key: str, index: int) -> None: ...


class RecorderDelegate(RecorderDelegateProtocol):
    def __init__(self, logger: typing.Optional[RecorderLogger] = None) -> None:
        self.__logger: RecorderLogger = logger if logger is not None else RecorderLogger()

    def property_changed(self, accessor: Accessor, key: str, value: typing.Any) -> None:
        self.__logger.append(KeyRecorderEntry(accessor, key, value))

    def set_item(self, accessor: Accessor, key: str, item: typing.Any) -> None:
        self.__logger.append(KeyRecorderEntry(accessor, key, copy.deepcopy(item)))

    def insert_item(self, accessor: Accessor, key: str, index: int, item: typing.Any) -> None:
        self.__logger.append(InsertRecorderEntry(accessor, key, index, copy.deepcopy(item)))

    def remove_item(self, accessor: Accessor, key: str, index: int) -> None:
        self.__logger.append(RemoveRecorderEntry(accessor, key, index))


class Recorder:
    """Record changes to an observable object.

    The Accessor describe how to access the object from a root object.

    The RecorderEntry describes how to change the object.
    """

    # TODO: make changes resilient... what happens if underlying object changes and recorder can't be applied?
    # TODO: thread safety

    def __init__(self, object: typing.Any, accessor: typing.Optional[Accessor] = None, logger: typing.Optional[RecorderLogger] = None, delegate: typing.Optional[RecorderDelegateProtocol] = None) -> None:
        self.__weak_object = weakref.ref(object)
        self.__accessor = accessor or DirectAccessor()
        self.__logger: typing.Optional[RecorderLogger] = None
        if delegate:
            assert logger is None
            self.__delegate = delegate
        else:
            self.__logger = logger if logger is not None else RecorderLogger()
            self.__delegate = RecorderDelegate(self.__logger)
        self.__property_changed_event_listener = object.property_changed_event.listen(weak_partial(Recorder.__property_changed, self, weakref.ref(object)))
        self.__item_set_event_listener = object.item_set_event.listen(weak_partial(Recorder.__item_set, self))
        self.__item_cleared_event_listener = object.item_cleared_event.listen(weak_partial(Recorder.__item_cleared, self))
        self.__item_inserted_event_listener = object.item_inserted_event.listen(weak_partial(Recorder.__item_inserted, self))
        self.__item_removed_event_listener = object.item_removed_event.listen(weak_partial(Recorder.__item_removed, self))
        self.__item_recorders: typing.Dict[str, Recorder] = dict()
        self.__relationship_recorders = collections.defaultdict(list)
        for key in object.item_names:
            item = getattr(object, key)
            if item:
                self.__item_recorders[key] = Recorder(item, KeyAccessor(self.__accessor, key), delegate=self.__delegate)
        for key in object.relationship_names:
            items = getattr(object, key)
            for index, item in enumerate(items):
                self.__relationship_recorders[key].append(Recorder(item, IndexAccessor(KeyAccessor(self.__accessor, key), index), delegate=self.__delegate))

    def close(self) -> None:
        pass

    def apply(self, object: Observable.Observable) -> None:
        assert self.__logger
        self.__logger.apply(object)

    @property
    def _accessor(self) -> Accessor:
        return self.__accessor

    @_accessor.setter
    def _accessor(self, value: Accessor) -> None:
        self.__accessor = value

    # Python 3.9+: o_ref: weakref.ReferenceType[typing.Any]
    def __property_changed(self, o_ref: typing.Any, key: str) -> None:
        object = o_ref()
        if object:
            if not hasattr(object, "_is_persistent_property_recordable") or object._is_persistent_property_recordable(key):
                self.__delegate.property_changed(self.__accessor, key, getattr(object, key))

    def __item_set(self, key: str, item: typing.Any) -> None:
        object = self.__weak_object()
        if hasattr(object, "relationship_names") and key not in getattr(object, "item_names"):
            return
        self.__item_recorders.pop(key)
        if item:
            self.__item_recorders[key] = Recorder(item, KeyAccessor(self.__accessor, key), delegate=self.__delegate)
        self.__delegate.set_item(self.__accessor, key, item)

    def __item_cleared(self, key: str) -> None:
        self.__item_set(key, None)

    def __item_inserted(self, key: str, value: typing.Any, before_index: int) -> None:
        object = self.__weak_object()
        if hasattr(object, "relationship_names") and key not in getattr(object, "relationship_names"):
            return
        for index, relationship_recorder in enumerate(self.__relationship_recorders[key]):
            if index >= before_index:
                relationship_recorder._accessor = IndexAccessor(KeyAccessor(self.__accessor, key), index + 1)
        self.__relationship_recorders[key].insert(before_index, Recorder(value, IndexAccessor(KeyAccessor(self.__accessor, key), before_index), delegate=self.__delegate))
        self.__delegate.insert_item(self.__accessor, key, before_index, value)

    def __item_removed(self, key: str, value: typing.Any, item_index: int) -> None:
        object = self.__weak_object()
        if hasattr(object, "relationship_names") and key not in getattr(object, "relationship_names"):
            return
        for index, relationship_recorder in enumerate(self.__relationship_recorders[key]):
            if index > item_index:
                relationship_recorder._accessor = IndexAccessor(KeyAccessor(self.__accessor, key), index - 1)
        self.__relationship_recorders[key].pop(item_index)
        self.__delegate.remove_item(self.__accessor, key, item_index)

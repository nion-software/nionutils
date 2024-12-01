"""List and filtered list model."""

from __future__ import annotations

# standard libraries
import contextlib
import copy
import operator
import threading
import types
import typing

# third party libraries
# None

# local libraries
from nion.utils import Event
from nion.utils import Observable
from nion.utils import Selection
from .ReferenceCounting import weak_partial

T = typing.TypeVar('T')


class ListModelLike(typing.Protocol):
    @property
    def item_inserted_event(self) -> Event.Event: return typing.cast(Event.Event, None)

    @property
    def item_removed_event(self) -> Event.Event: return typing.cast(Event.Event, None)

    @property
    def items(self) -> typing.Sequence[typing.Any]: return list()


class ListModel(Observable.Observable, typing.Generic[T]):

    def __init__(self, key: typing.Optional[str] = None, items: typing.Optional[typing.Sequence[T]] = None) -> None:
        super().__init__()
        self.__key = key
        self.__items : typing.List[T] = list(items) if items else list()

    def close(self) -> None:
        pass

    def clear_items(self) -> None:
        while self.__items:
            self.remove_item(len(self.__items) - 1)

    def insert_item(self, index: int, value: T) -> None:
        self.__items.insert(index, value)
        self.notify_insert_item(self.__key if self.__key else "items", value, index)

    def remove_item(self, index: int) -> None:
        self.pop_item(index)

    def append_item(self, value: T) -> None:
        self.insert_item(len(self.__items), value)

    def pop_item(self, index: int) -> T:
        value = self.__items[index]
        del self.__items[index]
        self.notify_remove_item(self.__key if self.__key else "items", value, index)
        return value

    @property
    def items(self) -> typing.Sequence[T]:
        return self.__items

    @items.setter
    def items(self, items: typing.Sequence[T]) -> None:
        self.clear_items()
        for item in items:
            self.insert_item(len(self.__items), item)

    @property
    def count(self) -> int:
        return len(self.__items)

    @property
    def _items(self) -> typing.List[T]:
        return self.__items

    def __getattr__(self, item: str) -> typing.Sequence[T]:
        if self.__key and item == self.__key:
            return self.items
        raise AttributeError(item)


class Filter:
    def __init__(self, default: bool = False) -> None:
        self.__default = default

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> Filter:
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        result.__default = self.__default
        return result

    def matches(self, d: typing.Any) -> bool:
        return self.__default


class AndFilter(Filter):
    def __init__(self, filters: typing.Optional[typing.Sequence[Filter]] = None) -> None:
        super().__init__()
        self.__filters = copy.copy(filters) if filters else list()

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> AndFilter:
        result = typing.cast(AndFilter, super().__deepcopy__(memo))
        result.__filters = copy.deepcopy(self.__filters, memo)
        return result

    def matches(self, d: typing.Any) -> bool:
        return all(map(operator.methodcaller('matches', d), self.__filters))


class OrFilter(Filter):
    def __init__(self, filters: typing.Optional[typing.Sequence[Filter]] = None) -> None:
        super().__init__()
        self.__filters = copy.copy(filters) if filters else list()

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> OrFilter:
        result = typing.cast(OrFilter, super().__deepcopy__(memo))
        result.__filters = copy.deepcopy(self.__filters, memo)
        return result

    def matches(self, d: typing.Any) -> bool:
        return any(map(operator.methodcaller('matches', d), self.__filters))


class NotFilter(Filter):
    def __init__(self, filter: Filter) -> None:
        super().__init__()
        self.__filter = filter

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> NotFilter:
        result = typing.cast(NotFilter, super().__deepcopy__(memo))
        result.__filter = copy.deepcopy(self.__filter, memo)
        return result

    def matches(self, d: typing.Any) -> bool:
        return not self.__filter.matches(d)


class EqFilter(Filter):
    def __init__(self, key: str, value: typing.Any, cmp: typing.Optional[EqualityOperator] = None) -> None:
        super().__init__()
        self.__key = key
        self.__value = value
        self.__cmp = cmp if cmp else typing.cast(EqualityOperator, operator.eq)

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> EqFilter:
        result = typing.cast(EqFilter, super().__deepcopy__(memo))
        result.__key = self.__key
        result.__value = self.__value
        result.__cmp = self.__cmp
        return result

    def matches(self, d: typing.Any) -> bool:
        d_value = getattr(d, self.__key)
        return self.__cmp(d_value, self.__value)


class NotEqFilter(Filter):
    def __init__(self, key: str, value: typing.Any, cmp: typing.Optional[EqualityOperator] = None) -> None:
        super().__init__()
        self.__key = key
        self.__value = value
        self.__cmp = cmp if cmp else operator.eq

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> NotEqFilter:
        result = typing.cast(NotEqFilter, super().__deepcopy__(memo))
        result.__key = self.__key
        result.__value = self.__value
        result.__cmp = self.__cmp
        return result

    def matches(self, d: typing.Any) -> bool:
        d_value = getattr(d, self.__key)
        return not self.__cmp(d_value, self.__value)


class StartsWithFilter(Filter):
    def __init__(self, key: str, value: str) -> None:
        super().__init__()
        self.__key = key
        self.__value = value

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> StartsWithFilter:
        result = typing.cast(StartsWithFilter, super().__deepcopy__(memo))
        result.__key = self.__key
        result.__value = self.__value
        return result

    def matches(self, d: typing.Any) -> bool:
        d_value = getattr(d, self.__key)
        return bool(d_value.startswith(self.__value))


class TextFilter(Filter):
    def __init__(self, key: str, text: str) -> None:
        super().__init__()
        self.__key = key
        self.__text = text
        self.__lower_text = text.lower()

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> TextFilter:
        result = typing.cast(TextFilter, super().__deepcopy__(memo))
        result.__key = self.__key
        result.__text = self.__text
        return result

    def matches(self, d: typing.Any) -> bool:
        d_value = str(getattr(d, self.__key)).lower()
        return d_value.find(self.__lower_text) >= 0


class PartialDateFilter(Filter):
    def __init__(self, key: str, year: typing.Optional[int] = None, month: typing.Optional[int] = None,
                 day: typing.Optional[int] = None) -> None:
        super().__init__()
        self.__key = key
        self.__year = year
        self.__month = month
        self.__day = day

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> PartialDateFilter:
        result = typing.cast(PartialDateFilter, super().__deepcopy__(memo))
        result.__key = self.__key
        result.__year = self.__year
        result.__month = self.__month
        result.__day = self.__day
        return result

    def matches(self, d: typing.Any) -> bool:
        d_value = getattr(d, self.__key)
        if self.__year and d_value.year != self.__year:
            return False
        if self.__month and d_value.month != self.__month:
            return False
        if self.__day and d_value.day != self.__day:
            return False
        return True


class PredicateFilter(Filter):
    # used for testing, not serializable
    def __init__(self, predicate: typing.Callable[[typing.Any], bool]) -> None:
        super().__init__()
        self.__predicate = predicate

    def __deepcopy__(self, memo: typing.Dict[typing.Any, typing.Any]) -> PredicateFilter:
        result = typing.cast(PredicateFilter, super().__deepcopy__(memo))
        result.__predicate = self.__predicate
        return result

    def matches(self, d: typing.Any) -> bool:
        return self.__predicate(d)


SortKeyCallable = typing.Callable[[typing.Any], typing.Any]
OptionalSortKeyCallable = typing.Optional[SortKeyCallable]
SortOperator = typing.Callable[[typing.Any, typing.Any], typing.Any]
EqualityOperator = typing.Callable[[typing.Any, typing.Any], bool]


class FilteredListModel(Observable.Observable):
    """Filtered list of items.

    This class implements a filter function and a sorting function. Both the filter and
    sorting can be changed on the fly and this class will generate the appropriate insert
    and remove messages.

    When making multiple changes, it is best to use the begin_change and end_change methods
    to bracket the changes. This allows the updating of the items to occur only once via the
    '__update_items' method. The 'changes' context manager can also be used to bracket changes.

    In cases where a listener wants to receive all changes at once, the listener can listen
    to the begin_changes and end_changes events, gathering any changes that occur between the
    events and handle them at the end changes event.
    """

    def __init__(self, *, container: typing.Optional[Observable.Observable] = None,
                 master_items_key: typing.Optional[str] = None, items_key: typing.Optional[str] = None,
                 selection: typing.Optional[Selection.IndexedSelection] = None) -> None:
        super().__init__()
        self.__container = None
        self.__master_items_key = master_items_key or items_key or "items"
        self.__items_key = items_key or "items"
        self.__master_items = list[typing.Any]()  # a list of source items (to be filtered)
        self.__items = list[typing.Any]()  # a list of filtered items
        self.__item_sort_keys = dict[typing.Any, typing.Any]()  # list of sort keys for items at the time added
        self.__items_sorted = False  # whether items are currently sorted
        self._update_mutex = threading.RLock()
        self.__filter = Filter(True)
        self.__sort_key: OptionalSortKeyCallable = None
        self.__sort_reverse = False
        self.__change_level = 0
        self.__needs_update_items = False
        self.begin_changes_event = Event.Event()
        self.end_changes_event = Event.Event()
        self.__item_changed_event_listeners: typing.List[typing.Optional[Event.EventListener]] = list()
        self.__item_inserted_event_listener: typing.Optional[Event.EventListener] = None
        self.__item_removed_event_listener: typing.Optional[Event.EventListener] = None
        self.__item_content_changed_event_listener: typing.Optional[Event.EventListener] = None
        self.__begin_changes_event_listener: typing.Optional[Event.EventListener] = None
        self.__end_changes_event_listener: typing.Optional[Event.EventListener] = None
        self.__selection_changes: typing.List[typing.Tuple[bool, int]] = list()
        self.__selections = list()
        if selection:
            self.__selections.append(selection)
        self.container = container

    def close(self) -> None:
        pass

    def begin_change(self) -> None:
        """ Begin a set of changes. Balance with end_changes. """
        if self.__change_level == 0:
            self.begin_changes_event.fire(self.__items_key)
        self.__change_level += 1

    def end_change(self) -> None:
        """ End a set of changes and update items if finished. """
        with self._update_mutex:
            self.__change_level -= 1
            if self.__change_level == 0:
                if self.__needs_update_items:
                    self.__update_items()
                    self.__needs_update_items = False
                self.end_changes_event.fire(self.__items_key)

    class ChangeTracker:
        def __init__(self, list_model: FilteredListModel) -> None:
            self.list_model = list_model

        def __enter__(self) -> FilteredListModel.ChangeTracker:
            self.list_model.begin_change()
            return self

        def __exit__(self, exception_type: typing.Optional[typing.Type[BaseException]],
                     value: typing.Optional[BaseException], traceback: typing.Optional[types.TracebackType]) -> typing.Optional[bool]:
            self.list_model.end_change()
            return None

    def changes(self) -> contextlib.AbstractContextManager[FilteredListModel.ChangeTracker]:
        """ Acquire this while setting filter or sort so that changes get made simultaneously. """
        return FilteredListModel.ChangeTracker(self)

    # thread safe.
    @property
    def sort_key(self) -> OptionalSortKeyCallable:
        """ Return the sort key function (for item). """
        return self.__sort_key

    @sort_key.setter
    def sort_key(self, value: OptionalSortKeyCallable) -> None:
        """ Set the sort key function. """
        with self._update_mutex:
            self.__sort_key = value
            self.__items_sorted = False
        with self.changes():
            self.__needs_update_items = True

    @property
    def sort_reverse(self) -> bool:
        """ Return the sort reverse value. """
        return self.__sort_reverse

    @sort_reverse.setter
    def sort_reverse(self, value: bool) -> None:
        """ Set the sort reverse value. """
        with self._update_mutex:
            self.__sort_reverse = value
            self.__items_sorted = False
        with self.changes():
            self.__needs_update_items = True

    # thread safe.
    @property
    def filter(self) -> Filter:
        """ Return the filter function. """
        return self.__filter

    @filter.setter
    def filter(self, value: Filter) -> None:
        """ Set the filter function. """
        self.__filter = value
        self.__items_sorted = False
        with self.changes():
            self.__needs_update_items = True

    @property
    def items(self) -> typing.Sequence[typing.Any]:
        """ Return the items. """
        with self._update_mutex:
            return copy.copy(self.__items)

    @property
    def item_count(self) -> int:
        """ Return the number of items. """
        return len(self.__items)

    def __getattr__(self, item: str) -> typing.Any:
        if item == self.__items_key:
            return self.items
        raise AttributeError()

    # thread safe
    def _get_master_items(self) -> typing.Sequence[typing.Any]:
        with self._update_mutex:
            return copy.copy(self.__master_items)

    def __get_sort_key(self, item: typing.Any) -> typing.Any:
        sort_key = self.__item_sort_keys.get(item)
        if sort_key is None:
            sort_key = self.sort_key(item) if self.sort_key else None
        return sort_key

    def __find_sorted_index_for_item(self, item: typing.Any, items: typing.Sequence[typing.Any], sort_key: SortKeyCallable, sort_reverse: bool) -> int:
        sort_operator = operator.gt if sort_reverse else operator.lt
        item_sort_key = sort_key(item)
        low = 0
        high = len(items)
        while low < high:
            mid = (low + high) // 2
            if sort_operator(sort_key(items[mid]), item_sort_key):
                low = mid + 1
            else:
                high = mid
        return low

    def __find_unsorted_index_for_item(self, item: typing.Any, master_items: typing.Sequence[typing.Any], filter: Filter) -> int:
        index = 0
        for item_ in master_items:
            if item_ == item:
                break
            if filter.matches(item_):
                index += 1
        return index

    # thread safe
    def __changed_master_item(self, index: int, item: typing.Any) -> None:
        # item is in the list and the filter matches and index will not change.
        # notify item content changed for listeners. don't update the selection.
        self.__item_sort_keys[item] = self.sort_key(item) if self.sort_key else None
        self.notify_item_content_changed(self.__items_key, item, index)

    def __insert_item(self, item: typing.Any) -> None:
        # insert an item by finding its item index and inserting it.
        items = self.__items
        sort_key = self.sort_key
        if self.__items_sorted and sort_key:
            before_index = self.__find_sorted_index_for_item(item, items, self.__get_sort_key, self.sort_reverse)
        else:
            before_index = self.__find_unsorted_index_for_item(item, self._get_master_items(), self.filter)
        self.__insert_item_at_index(item, before_index)

    def __insert_item_at_index(self, item: typing.Any, before_index: int) -> None:
        # insert an item at the given index, notify, and update selections.
        self.__items.insert(before_index, item)
        self.__item_sort_keys[item] = self.sort_key(item) if self.sort_key else None
        self.notify_insert_item(self.__items_key, item, before_index)
        # only update the selection here if there is no end changes event listener.
        # if there is a listener, updating the selection is done in end changes.
        self.__selection_changes.append((True, before_index))
        if not self.__end_changes_event_listener:
            for selection in self.__selections:
                selection.insert_index(before_index)

    def __remove_item(self, item: typing.Any) -> None:
        # remove an item by finding its index and removing it.
        sort_key = self.sort_key
        if self.__items_sorted and sort_key:
            index = self.__find_sorted_index_for_item(item, self.__items, self.__get_sort_key, self.sort_reverse)
        else:
            index = self.__items.index(item)
        self.__remove_item_at_index(index)

    def __remove_item_at_index(self, item_index: int) -> None:
        # remove an item at the given index, notify, and update selections.
        item = self.__items.pop(item_index)
        self.__item_sort_keys.pop(item, None)
        self.notify_remove_item(self.__items_key, item, item_index)
        # only update the selection here if there is no end changes event listener.
        # if there is a listener, updating the selection is done in end changes.
        self.__selection_changes.append((False, item_index))
        if not self.__end_changes_event_listener:
            for selection in self.__selections:
                selection.remove_index(item_index)

    # thread safe
    def __master_item_changed(self, item: typing.Any) -> None:
        # when an item is changed it may have a new sort key. call the insert/remove to reflect the change in items.
        with self._update_mutex:
            items = self.__items
            # item will be in master item list already
            was_item_included = item in items
            if self.filter.matches(item):
                # item will be in the items list
                sort_key = self.sort_key
                if self.__items_sorted and sort_key:
                    if was_item_included:
                        with self.changes():
                            index = items.index(item)
                            items_copy = items[0:index] + items[index + 1:]
                            self.__item_sort_keys.pop(items[index])
                            # NOTE: new_index will be the index with the old item removed
                            new_index = self.__find_sorted_index_for_item(item, items_copy, self.__get_sort_key, self.sort_reverse)
                            if new_index < index:
                                self.__remove_item_at_index(index)
                                self.__insert_item_at_index(item, new_index)
                            elif new_index > index:
                                self.__remove_item_at_index(index)
                                self.__insert_item_at_index(item, new_index)
                            else:
                                self.__changed_master_item(index, item)
                    else:
                        # item was not in list
                        with self.changes():
                            new_index = self.__find_sorted_index_for_item(item, items, self.__get_sort_key, self.sort_reverse)
                            self.__insert_item_at_index(item, new_index)
                else:
                    # items are not sorted
                    if not was_item_included:
                        with self.changes():
                            before_index = self.__find_unsorted_index_for_item(item, self._get_master_items(), self.filter)
                            self.__insert_item_at_index(item, before_index)
            else:
                # item should be removed from items list if it exists
                if was_item_included:
                    with self.changes():
                        self.__remove_item_at_index(items.index(item))

    # thread safe.
    def __update_items(self) -> None:
        """Build the items and generate change messages.

        Builds the items from the master item list, then generates a sequence of
         inserter and remover calls representing the changes from the previous list.
        """
        with self._update_mutex:
            # first build the new items list, including items with master item.
            filtered_items = filter(self.filter.matches, self.__master_items)
            # now generate the insert/remove instructions to make the official
            # list match the proposed list.
            # disable asserts for performance
            # assert len(set(self._get_master_items())) == len(self._get_master_items())
            # assert len(set(items)) == len(items)
            sort_key = self.sort_key
            if sort_key and self.__items_sorted:
                old_items_set = set(self.__items)
                new_items_set = set(filtered_items)
                insert_items_set = new_items_set - old_items_set
                remove_items_set = old_items_set - new_items_set
                # remove old items by iterating through all and checking whether in remove items set
                for item in remove_items_set:
                    self.__remove_item(item)
                # insert using sorting
                for item in insert_items_set:
                    self.__insert_item(item)
            else:
                sorted_items = sorted(filtered_items, key=sort_key, reverse=self.sort_reverse) if sort_key else filtered_items
                # requires sorting and not already sorted or not sorted: fall back to full replacement
                for _ in range(len(self.__items)):
                    self.__remove_item_at_index(0)
                for index, item in enumerate(sorted_items):
                    self.__insert_item_at_index(item, index)
            self.__items_sorted = True

    # thread safe.
    @property
    def container(self) -> typing.Optional[Observable.Observable]:
        return self.__container

    # thread safe.
    @container.setter
    def container(self, container: typing.Optional[Observable.Observable]) -> None:
        self.set_container_filter_sort(container, self.__filter, self.__sort_key, self.__sort_reverse)

    def set_container_filter_sort(self, container: typing.Optional[Observable.Observable], new_filter: Filter, sort_key: OptionalSortKeyCallable, sort_reverse: bool) -> None:
        # set all at once to avoid multiple updates.
        with self._update_mutex:
            new_master_items = getattr(container, self.__master_items_key) if container else list()

            # update the content listeners on master items
            self.__item_changed_event_listeners.clear()
            for master_item in new_master_items:
                item_changed_event_listener = master_item.item_changed_event.listen(weak_partial(FilteredListModel.__master_item_changed, self, master_item)) if hasattr(master_item, "item_changed_event") else None
                self.__item_changed_event_listeners.append(item_changed_event_listener)

            # update the master items
            self.__master_items = list(new_master_items)

            # update listeners on the container
            self.__item_inserted_event_listener = None
            self.__item_removed_event_listener = None
            self.__item_content_changed_event_listener = None
            self.__begin_changes_event_listener = None
            self.__end_changes_event_listener = None

            # update the container by adding listeners where necessary or available
            self.__container = container
            if self.__container:
                self.__item_inserted_event_listener = self.__container.item_inserted_event.listen(weak_partial(FilteredListModel.__container_item_inserted, self))
                self.__item_removed_event_listener = self.__container.item_removed_event.listen(weak_partial(FilteredListModel.__container_item_removed, self))
                self.__item_content_changed_event_listener = self.__container.item_content_changed_event.listen(weak_partial(FilteredListModel.__container_item_content_changed, self))

                if hasattr(self.__container, "begin_changes_event") and hasattr(self.__container, "end_changes_event"):

                    def begin_changes(list_model: FilteredListModel, key: str) -> None:
                        if key == list_model.__master_items_key:
                            list_model.begin_changes_event.fire(list_model.__items_key)

                    def end_changes(list_model: FilteredListModel, key: str) -> None:
                        if key == list_model.__master_items_key:
                            list_model.end_changes_event.fire(list_model.__items_key)
                        for selection in list_model.__selections:
                            selection_copy = copy.copy(selection)
                            for do_insert, index in list_model.__selection_changes:
                                # adjust the selection copy for the new index, but don't add/remove the new index itself.
                                # leaves the selected items the same.
                                if do_insert:
                                    selection_copy.insert_index(index)
                                else:
                                    selection_copy.remove_index(index)
                            selection.set_multiple(selection_copy.indexes)
                        list_model.__selection_changes = list()

                    self.__begin_changes_event_listener = self.__container.begin_changes_event.listen(weak_partial(begin_changes, self))
                    self.__end_changes_event_listener = self.__container.end_changes_event.listen(weak_partial(end_changes, self))

            # note: difflib.SequenceMatcher will not work here because it does not guarantee that an item does not
            # appear in the list at any intermediate step and duplicate items are not possible because downstream
            # filters cannot handle duplicate items (think about removing a matching item without an index).

            with self.changes():
                self.__filter = new_filter
                self.__sort_key = sort_key
                self.__sort_reverse = sort_reverse
                self.__items_sorted = False  # required for update items
                self.__needs_update_items = True

    def make_selection(self) -> Selection.IndexedSelection:
        selection = Selection.IndexedSelection()
        self.__selections.append(selection)
        return selection

    def release_selection(self, selection: Selection.IndexedSelection) -> None:
        self.__selections.remove(selection)

    def __container_item_inserted(self, key: str, item: typing.Any, before_index: int) -> None:
        # when an item is inserted into the container, it may be added to the items list.
        if key == self.__master_items_key:
            with self.changes():
                with self._update_mutex:
                    assert item is None or not item in self.__master_items, f"{item} already in {self.__master_items}"
                    self.__master_items.insert(before_index, item)
                    item_changed_event_listener = item.item_changed_event.listen(weak_partial(FilteredListModel.__master_item_changed, self, item)) if hasattr(item, "item_changed_event") else None
                    self.__item_changed_event_listeners.insert(before_index, item_changed_event_listener)
                    if self.filter.matches(item):
                        self.__insert_item(item)

    def __container_item_removed(self, key: str, item: typing.Any, index: int) -> None:
        # when an item is removed from the container, it may be removed from the items list.
        if key == self.__master_items_key:
            with self.changes():
                with self._update_mutex:
                    del self.__master_items[index]
                    del self.__item_changed_event_listeners[index]
                    if item in self.__items:
                        self.__remove_item(item)

    def __container_item_content_changed(self, key: str, item: typing.Any, index: int) -> None:
        # when an item is changed in the container, it may be updated in the items list.
        if key == self.__master_items_key:
            self.__master_item_changed(item)


class MappedListModel(Observable.Observable):
    _MapFunctionType = typing.Callable[[typing.Any], typing.Any]

    def __init__(self, *, container: typing.Optional[Observable.Observable] = None,
                 master_items_key: typing.Optional[str] = None, items_key: typing.Optional[str] = None,
                 map_fn: typing.Optional[MappedListModel._MapFunctionType] = None,
                 unmap_fn: typing.Optional[MappedListModel._MapFunctionType] = None,
                 selection: typing.Optional[Selection.IndexedSelection] = None) -> None:
        super().__init__()
        self.__container = None
        self.__master_items_key = master_items_key or "items"
        self.__items_key = items_key or self.__master_items_key
        self.__map_fn = map_fn or (lambda x: x)
        self.__unmap_fn = unmap_fn or (lambda x: x)
        self.__items: typing.List[typing.Any] = list()  # a list of transformed items
        self._update_mutex = threading.RLock()
        self.__change_level = 0
        self.begin_changes_event = Event.Event()
        self.end_changes_event = Event.Event()
        self.__item_inserted_event_listener = None
        self.__item_removed_event_listener = None
        self.__begin_changes_event_listener = None
        self.__end_changes_event_listener = None
        self.__selections = list()
        if selection:
            self.__selections.append(selection)
        self.container = container

    def close(self) -> None:
        pass

    def begin_change(self) -> None:
        """ Begin a set of changes. Balance with end_changes. """
        if self.__change_level == 0:
            self.begin_changes_event.fire(self.__items_key)
        self.__change_level += 1

    def end_change(self) -> None:
        """ End a set of changes and update items if finished. """
        with self._update_mutex:
            self.__change_level -= 1
            if self.__change_level == 0:
                self.end_changes_event.fire(self.__items_key)

    class ChangeTracker:
        def __init__(self, list_model: MappedListModel):
            self.list_model = list_model

        def __enter__(self) -> MappedListModel.ChangeTracker:
            self.list_model.begin_change()
            return self

        def __exit__(self, exception_type: typing.Optional[typing.Type[BaseException]],
                     value: typing.Optional[BaseException], traceback: typing.Optional[types.TracebackType]) -> typing.Optional[bool]:
            self.list_model.end_change()
            return None

    def changes(self) -> contextlib.AbstractContextManager[MappedListModel.ChangeTracker]:
        """ Acquire this while setting filter or sort so that changes get made simultaneously. """
        return MappedListModel.ChangeTracker(self)

    def mark_changed(self) -> None:
        with self.changes(): pass

    @property
    def items(self) -> typing.Sequence[typing.Any]:
        """ Return the items. """
        with self._update_mutex:
            return copy.copy(self.__items)

    @property
    def items_key(self) -> str:
        return self.__items_key

    def __getattr__(self, item: str) -> typing.Any:
        if item == self.__items_key:
            return self.items
        raise AttributeError()

    # thread safe.
    @property
    def container(self) -> typing.Optional[Observable.Observable]:
        return self.__container

    # thread safe.
    @container.setter
    def container(self, container: typing.Optional[Observable.Observable]) -> None:
        # remove old master items
        if self.__container:
            self.__item_inserted_event_listener = None
            self.__item_removed_event_listener = None
            self.__begin_changes_event_listener = None
            self.__end_changes_event_listener = None
            for item in reversed(copy.copy(getattr(self.__container, self.__master_items_key))):
                self.__master_item_removed(self.__master_items_key, item, len(self.__items) - 1)
        # add new master items
        self.__container = container
        if self.__container:
            self.__item_inserted_event_listener = self.__container.item_inserted_event.listen(weak_partial(MappedListModel.__master_item_inserted, self))
            self.__item_removed_event_listener = self.__container.item_removed_event.listen(weak_partial(MappedListModel.__master_item_removed, self))
            if hasattr(self.__container, "begin_changes_event") and hasattr(self.__container, "end_changes_event"):

                def begin_changes(list_model: FilteredListModel, key: str) -> None:
                    if key == list_model.__master_items_key:
                        list_model.begin_change()

                def end_changes(list_model: FilteredListModel, key: str) -> None:
                    if key == list_model.__master_items_key:
                        list_model.end_change()

                self.__begin_changes_event_listener = self.__container.begin_changes_event.listen(weak_partial(begin_changes, self))
                self.__end_changes_event_listener = self.__container.end_changes_event.listen(weak_partial(end_changes, self))
            for index, item in enumerate(getattr(self.__container, self.__master_items_key)):
                self.__master_item_inserted(self.__master_items_key, item, index)

    def make_selection(self) -> Selection.IndexedSelection:
        selection = Selection.IndexedSelection()
        self.__selections.append(selection)
        return selection

    def release_selection(self, selection: Selection.IndexedSelection) -> None:
        self.__selections.remove(selection)

    # thread safe.
    def __master_item_inserted(self, key: str, item: typing.Any, before_index: int) -> None:
        """ Insert the item. Called from the container. """
        if key == self.__master_items_key:
            with self._update_mutex:
                mapped_item = self.__map_fn(item)
                self.__items.insert(before_index, mapped_item)
                self.notify_insert_item(self.__items_key, mapped_item, before_index)
                for selection in self.__selections:
                    selection.insert_index(before_index)

    # thread safe.
    def __master_item_removed(self, key: str, item: typing.Any, index: int) -> None:
        """ Remove the item. Called from the container. """
        if key == self.__master_items_key:
            with self._update_mutex:
                mapped_item = self.__items[index]
                if callable(self.__unmap_fn):
                    self.__unmap_fn(mapped_item)
                del self.__items[index]
                self.notify_remove_item(self.__items_key, mapped_item, index)
                for selection in self.__selections:
                    selection.remove_index(index)


class FlattenedListModel(Observable.Observable):
    """A flattened list model (list of lists).

    Watches child items in the master items in the container and flattens them into a list.
    """

    def __init__(self, *, master_items_key: str, container: typing.Optional[Observable.Observable] = None,
                 child_items_key: typing.Optional[str] = None, items_key: typing.Optional[str] = None,
                 selection: typing.Optional[Selection.IndexedSelection] = None) -> None:
        super().__init__()
        self.__container = None
        self.__master_items_key = master_items_key
        self.__child_items_key = child_items_key or "items"
        self.__items_key = items_key or self.__child_items_key
        self.__master_items : typing.List[typing.Any] = list()  # a list of master items (to be transformed)
        self.__items : typing.List[typing.Any] = list()  # a list of flattened items
        self.__children: typing.Dict[typing.Any, typing.List[typing.Any]] = dict()  # map master item to children
        self._update_mutex = threading.RLock()
        self.__item_inserted_event_listener = None
        self.__item_removed_event_listener = None
        self.__child_item_inserted_event_listener: typing.Dict[typing.Any, Event.EventListener] = dict()
        self.__child_item_removed_event_listener: typing.Dict[typing.Any, Event.EventListener] = dict()
        self.__selections = list()
        if selection:
            self.__selections.append(selection)
        self.container = container

    def close(self) -> None:
        pass

    @property
    def items(self) -> typing.Sequence[typing.Any]:
        """ Return the items. """
        with self._update_mutex:
            return copy.copy(self.__items)

    def __getattr__(self, item: str) -> typing.Any:
        if item == self.__items_key:
            return self.items
        raise AttributeError()

    # thread safe.
    @property
    def container(self) -> typing.Optional[Observable.Observable]:
        return self.__container

    # thread safe.
    @container.setter
    def container(self, container: typing.Optional[Observable.Observable]) -> None:
        # remove old master items
        if self.__container:
            self.__item_inserted_event_listener = None
            self.__item_removed_event_listener = None
            for item in reversed(copy.copy(getattr(self.__container, self.__master_items_key))):
                self.__master_item_removed(self.__master_items_key, item, len(self.__master_items) - 1)
        # add new master items
        self.__container = container
        if self.__container:
            self.__item_inserted_event_listener = self.__container.item_inserted_event.listen(weak_partial(FlattenedListModel.__master_item_inserted, self))
            self.__item_removed_event_listener = self.__container.item_removed_event.listen(weak_partial(FlattenedListModel.__master_item_removed, self))
            for index, item in enumerate(getattr(self.__container, self.__master_items_key)):
                self.__master_item_inserted(self.__master_items_key, item, index)

    def make_selection(self) -> Selection.IndexedSelection:
        selection = Selection.IndexedSelection()
        self.__selections.append(selection)
        return selection

    def release_selection(self, selection: Selection.IndexedSelection) -> None:
        self.__selections.remove(selection)

    # almost thread safe. assumes child items will not change duing this call.
    def __master_item_inserted(self, key: str, item: typing.Any, before_index: int) -> None:
        # insert a master item.
        # set up listeners for child item changes.
        # add any existing child item.
        if key == self.__master_items_key:
            with self._update_mutex:
                assert not item in self.__master_items, "master item already in " + str(self.__master_items_key) + " (" + str(self.__items_key) + " / " + str(self.__child_items_key) + ")"
                self.__master_items.insert(before_index, item)
                self.__child_item_inserted_event_listener[item] = item.item_inserted_event.listen(weak_partial(FlattenedListModel.__child_item_inserted, self, item))
                self.__child_item_removed_event_listener[item] = item.item_removed_event.listen(weak_partial(FlattenedListModel.__child_item_removed, self, item))
                for index, child_item in enumerate(getattr(item, self.__child_items_key)):
                    self.__child_item_inserted(item, self.__child_items_key, child_item, index)

    # thread safe.
    def __master_item_removed(self, key: str, item: typing.Any, index: int) -> None:
        # remove a master item.
        # remove any existing child items.
        # remove listeners for child items.
        if key == self.__master_items_key:
            with self._update_mutex:
                for index_, child_item in reversed(list(enumerate(getattr(item, self.__child_items_key)))):
                    self.__child_item_removed(item, self.__child_items_key, child_item, index_)
                del self.__master_items[index]
                del self.__child_item_inserted_event_listener[item]
                del self.__child_item_removed_event_listener[item]
                assert not item in self.__master_items, "master item still in " + str(self.__master_items_key) + " (" + str(self.__items_key) + " / " + str(self.__child_items_key) + ")"

    def __child_item_inserted(self, master_item: typing.Any, key: str, item: typing.Any, before_index: int) -> None:
        if key == self.__child_items_key:
            master_index = 0
            for master_item_ in self.__master_items:
                if master_item_ == master_item:
                    break
                master_index += len(self.__children.get(master_item_, list()))
            master_index += before_index
            self.__children.setdefault(master_item, list()).insert(before_index, item)
            self.__items.insert(master_index, item)
            self.notify_insert_item(self.__items_key, item, master_index)
            for selection in self.__selections:
                selection.insert_index(before_index)

    def __child_item_removed(self, master_item: typing.Any, key: str, item: typing.Any, index: int) -> None:
        if key == self.__child_items_key:
            master_index = 0
            for master_item_ in self.__master_items:
                if master_item_ == master_item:
                    break
                master_index += len(self.__children.get(master_item_, list()))
            master_index += index
            del self.__children[master_item][index]
            del self.__items[master_index]
            self.notify_remove_item(self.__items_key, item, master_index)
            for selection in self.__selections:
                selection.remove_index(master_index)


class ListPropertyModel(Observable.Observable):
    """Treat a list as a single value property.

    Watches for changes to the list and fires property changed events.

    Does not currently handle item content changes.
    """

    def __init__(self, list_model: ListModelLike) -> None:
        super().__init__()
        self.__list_model = list_model
        self.__item_inserted_event_listener = list_model.item_inserted_event.listen(weak_partial(ListPropertyModel.__item_inserted, self))
        self.__item_removed_event_listener = list_model.item_removed_event.listen(weak_partial(ListPropertyModel.__item_removed, self))

    def close(self) -> None:
        pass

    def __item_inserted(self, key: str, item: typing.Any, before_index: int) -> None:
        self.notify_property_changed("value")

    def __item_removed(self, key: str, item: typing.Any, index: int) -> None:
        self.notify_property_changed("value")

    @property
    def value(self) -> typing.Sequence[typing.Any]:
        return list(self.__list_model.items)


class ObservedListModel(Observable.Observable, typing.Generic[T]):
    """Provide a list model by observing a collection on another object."""

    def __init__(self, item_source: Observable.Observable, items_key: str):
        super().__init__()
        self.__item_source = item_source
        self.__items_key = items_key
        self.__item_inserted_listener = item_source.item_inserted_event.listen(weak_partial(ObservedListModel.__item_inserted, self))
        self.__item_removed_listener = item_source.item_removed_event.listen(weak_partial(ObservedListModel.__item_removed, self))

    def __item_inserted(self, key: str, item: T, before_index: int) -> None:
        if key == self.__items_key:
            self.notify_insert_item("items", item, before_index)

    def __item_removed(self, key: str, item: T, index: int) -> None:
        if key == self.__items_key:
            self.notify_remove_item("items", item, index)

    @property
    def items(self) -> typing.Sequence[T]:
        return typing.cast(typing.Sequence[T], getattr(self.__item_source, self.__items_key))

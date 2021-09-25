from __future__ import annotations

import functools
import threading
import typing
import weakref


def weak_partial(fn: typing.Callable, o: typing.Any, *args, **kwargs) -> typing.Any:
    def _call(o_ref: weakref.ReferenceType, *args, **kwargs):
        o_deref = o_ref() if o_ref else None
        if o_deref:
            return fn(o_deref, *args, **kwargs)
        return None

    return functools.partial(_call, weakref.ref(o) if o else None, *args, **kwargs)


class ReferenceCounted:
    count = 0  # useful for detecting leaks in tests

    def __init__(self) -> None:
        super().__init__()
        self.__ref_count = 0
        self.__ref_count_mutex = threading.RLock()  # access to the image
        self.__active = True
        ReferenceCounted.count += 1

    # Give subclasses a chance to clean up. This gets called when reference
    # count goes to 0, but before deletion.
    def about_to_delete(self) -> None:
        ReferenceCounted.count -= 1

    def ref(self):
        class RefContextManager(object):
            def __init__(self, item):
                self.__item = item
            def __enter__(self):
                self.__item.add_ref()
                return self.__item
            def __exit__(self, type, value, traceback):
                self.__item.remove_ref()
        return RefContextManager(self)

    # Anytime you store a reference to this item, call add_ref.
    # This allows the class to disconnect from its own sources
    # automatically when the reference count goes to zero.
    # required type of typing.Any loses type information. callers should use typing.cast.
    def add_ref(self) -> ReferenceCounted:
        with self.__ref_count_mutex:
            self.__ref_count += 1
        return self

    # Anytime you give up a reference to this item, call remove_ref.
    def remove_ref(self, check: bool = True) -> None:
        with self.__ref_count_mutex:
            assert self.__ref_count > 0, 'Reference counted object has no references'
            self.__ref_count -= 1
            if self.__active and self.__ref_count == 0 and check:
                self.__active = False
                self.about_to_delete()

    # Return the reference count, which should represent the number
    # of places that this DataItem is stored by a caller.
    @property
    def ref_count(self):
        return self.__ref_count
"""
    Model classes. Useful for bindings.
"""

# standard libraries
import asyncio
import operator
import threading

# third party libraries
# none

# local libraries
from . import Event
from . import Observable
from . import Stream


class PropertyModel(Observable.Observable):

    """
        Holds a value which can be observed for changes. The value can be any type that supports equality test.

        An optional on_value_changed method gets called when the value changes.
    """

    def __init__(self, value=None, cmp=None):
        super(PropertyModel, self).__init__()
        self.__value = value
        self.__cmp = cmp if cmp else operator.eq
        self.on_value_changed = None

    def close(self):
        self.on_value_changed = None

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if self.__value is None:
            not_equal = value is not None
        elif value is None:
            not_equal = self.__value is not None
        else:
            not_equal = not self.__cmp(value, self.__value)
        if not_equal:
            self.__value = value
            self.notify_property_changed("value")
            if self.on_value_changed:
                self.on_value_changed(value)


class FuncStreamValueModel(PropertyModel):
    """Converts a stream of functions to a property model, evaluated asynchronously, on a thread."""

    def __init__(self, value_func_stream: Stream.AbstractStream, event_loop: asyncio.AbstractEventLoop, value=None, cmp=None):
        super().__init__(value=value, cmp=cmp)
        self.__value_func_stream = value_func_stream.add_ref()
        self.__task = None
        self.__event_loop = event_loop

        def handle_value_func(value_func):
            async def evaluate_value_func():
                self.value = await event_loop.run_in_executor(None, value_func)
                self.notify_property_changed("value")
            if self.__task:
                self.__task.cancel()
                self.__task = None
            self.__task = event_loop.create_task(evaluate_value_func())

        self.__stream_listener = value_func_stream.value_stream.listen(handle_value_func)
        handle_value_func(self.__value_func_stream.value)

    def close(self):
        self.__stream_listener.close()
        self.__stream_listener = None
        self.__value_func_stream.remove_ref()
        self.__value_func_stream = None
        if self.__task:
            self.__task.cancel()
            self.__task = None
        self.__event_loop = None
        super().close()

    def _run_until_complete(self):
        if self.__task:
            self.__event_loop.run_until_complete(self.__task)

    def _evaluate_immediate(self):
        return self.__value_func_stream.value()


class StreamValueModel(PropertyModel):
    """Converts a stream to a property model."""

    def __init__(self, value_stream: Stream.AbstractStream, value=None, cmp=None):
        super().__init__(value=value, cmp=cmp)
        self.__value_stream = value_stream.add_ref()

        def handle_value(value):
            self.value = value

        self.__stream_listener = value_stream.value_stream.listen(handle_value)

        handle_value(value_stream.value)

    def close(self):
        self.__stream_listener.close()
        self.__stream_listener = None
        self.__value_stream.remove_ref()
        self.__value_stream = None
        super().close()


class AsyncPropertyModel(Observable.Observable):
    def __init__(self, calculate_fn):
        super().__init__()
        self.__dirty = True
        self.__value = None
        self.__value_lock = threading.RLock()
        self.__task = None
        self.__calculate_fn = calculate_fn
        self.__calculate_lock = threading.RLock()
        self.marked_dirty_event = Event.Event()
        self.state_changed_event = Event.Event()

    @property
    def value(self):
        return self.__value

    def set_value(self, value):
        self.__value = value
        self.__dirty = False
        self.property_changed_event.fire("value")

    def mark_dirty(self) -> None:
        self.__dirty = True
        self.marked_dirty_event.fire()

    def evaluate(self, event_loop) -> None:
        with self.__value_lock:
            if not self.__task:

                async def evaluate_async(event_loop):
                    await event_loop.run_in_executor(None, self.__calculate)

                self.state_changed_event.fire("begin")

                self.__task = event_loop.create_task(evaluate_async(event_loop))

    def get_value_immediate(self):
        self.state_changed_event.fire("begin")
        self.__calculate()
        return self.__value

    def __calculate(self) -> None:
        try:
            with self.__calculate_lock:
                if self.__dirty:
                    if callable(self.__calculate_fn):
                        value = self.__calculate_fn()
                    else:
                        value = None
                    self.__value = value
                    self.__dirty = False
                    self.property_changed_event.fire("value")
        finally:
            self.__task = None
            self.state_changed_event.fire("end")

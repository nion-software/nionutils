"""
Classes related to streams of values, used for reactive style programming.
"""
from __future__ import annotations

# standard libraries
import asyncio
import enum
import functools
import operator
import typing

# third party libraries
# None

# local libraries
from . import Event
from . import Observable
from . import ReferenceCounting


T = typing.TypeVar('T')
OptionalT = typing.Optional[T]

class AbstractStream(ReferenceCounting.ReferenceCounted, typing.Generic[T]):
    """A stream provides a value property and a value_stream event that fires when the value changes."""

    def __init__(self):
        super().__init__()
        self.value_stream = None

    @property
    def value(self) -> OptionalT:
        return None


class StreamTask:

    def __init__(self, task: typing.Optional[typing.Any] = None, event_loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        self.__task: typing.Optional[asyncio.Task] = None
        self.__event_loop = event_loop or asyncio.get_event_loop()
        if task:
            self.create_task(task)

    def clear(self) -> None:
        if self.__task:
            self.__task.cancel()
        self.__task = None

    @property
    def is_active(self) -> bool:
        return self.__task is not None

    def create_task(self, task: typing.Awaitable[None]) -> asyncio.Task:
        assert self.__task is None
        self.__task = self.__event_loop.create_task(task)

        def zero_task(t: asyncio.Task) -> None:
            self.__task = None

        self.__task.add_done_callback(zero_task)
        return self.__task


class ValueStream(AbstractStream[T]):
    """A stream that sends out value when value is set."""

    def __init__(self, value: OptionalT = None):
        super().__init__()
        # internal values
        self.__value = value
        # outgoing messages
        self.value_stream = Event.Event()

    @property
    def value(self) -> OptionalT:
        return self.__value

    @value.setter
    def value(self, value: OptionalT) -> None:
        if self.__value != value:
            self.send_value(value)

    def send_value(self, value: OptionalT) -> None:
        self.__value = value
        self._send_value()

    def _send_value(self) -> None:
        """Subclasses may override this to filter or modify."""
        self.value_stream.fire(self.value)


class MapStream(AbstractStream):
    """A stream that applies a function when input streams change."""

    def __init__(self, stream, value_fn):
        super().__init__()
        # outgoing messages
        self.value_stream = Event.Event()
        # references
        self.__stream = stream.add_ref()
        # initialize values
        self.__value = None

        # listen for display changes
        def update_value(new_value):
            new_value = value_fn(new_value)
            if new_value != self.__value:
                self.__value = new_value
                self.value_stream.fire(self.__value)

        self.__listener = stream.value_stream.listen(update_value)
        update_value(stream.value)

    def about_to_delete(self) -> None:
        self.__listener.close()
        self.__listener = None
        self.__stream.remove_ref()
        self.__stream = None
        self.__value = None
        super().about_to_delete()

    @property
    def value(self):
        return self.__value


class CombineLatestStream(AbstractStream):
    """A stream that produces a tuple of values when input streams change."""

    def __init__(self, stream_list, value_fn: typing.Callable[[typing.Tuple], typing.Any] = None):
        super().__init__()
        # outgoing messages
        self.value_stream = Event.Event()
        # references
        self.__stream_list = [stream.add_ref() for stream in stream_list]
        self.__value_fn = value_fn or (lambda *x: tuple(x))
        # initialize values
        self.__values = [None] * len(stream_list)
        self.__value = None
        # listen for display changes
        self.__listeners = dict()  # index
        for index, stream in enumerate(self.__stream_list):
            self.__listeners[index] = stream.value_stream.listen(functools.partial(self.__handle_stream_value, index))
            self.__values[index] = stream.value
        self.__values_changed()

    def about_to_delete(self) -> None:
        for index, stream in enumerate(self.__stream_list):
            self.__listeners[index].close()
            self.__listeners[index] = None
            self.__values[index] = None
            stream.remove_ref()
        self.__stream_list = typing.cast(typing.List, None)
        self.__listeners = typing.cast(typing.Dict[int, typing.Any], None)
        self.__values = typing.cast(typing.List, None)
        self.__value = None
        super().about_to_delete()

    def __handle_stream_value(self, index, value):
        self.__values[index] = value
        self.__values_changed()

    def __values_changed(self):
        self.__value = self.__value_fn(*self.__values)
        self.value_stream.fire(self.__value)

    @property
    def value(self):
        return self.__value


class DebounceValue:
    def __init__(self):
        self.value = None


class DebounceStream(AbstractStream):
    """A stream that produces latest value after a specified interval has elapsed."""

    def __init__(self, input_stream: AbstractStream, period: float, loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        super().__init__()
        self.value_stream = Event.Event()
        self.__input_stream = input_stream.add_ref()
        self.__period = period
        self.__last_time = 0
        self.__value_holder = DebounceValue()
        self.__listener = input_stream.value_stream.listen(self.__value_changed)
        self.__debounce_task = StreamTask()
        self.__value_changed(input_stream.value)

    def about_to_delete(self) -> None:
        self.__listener.close()
        self.__listener = None
        self.__input_stream.remove_ref()
        self.__input_stream = None
        self.__debounce_task.clear()
        self.__debounce_task = typing.cast(StreamTask, None)
        super().about_to_delete()

    def __value_changed(self, value):
        self.__value_holder.value = value
        if not self.__debounce_task.is_active:  # only trigger new task if necessary

            async def debounce_delay(period: float, value_stream: Event.Event, value_holder: DebounceValue) -> None:
                await asyncio.sleep(period)
                value_stream.fire(value_holder.value)

            self.__debounce_task.create_task(debounce_delay(self.__period, self.value_stream, self.__value_holder))

    @property
    def value(self):
        return self.__value_holder.value


class SampleValue:
    def __init__(self):
        self.value = None
        self.pending_value = None
        self.is_dirty = False

    def set_pending_value(self, value) -> None:
        self.pending_value = value
        self.is_dirty = True


class SampleStream(AbstractStream):
    """A stream that produces new values at a specified interval."""

    def __init__(self, input_stream: AbstractStream, period: float, loop: typing.Optional[asyncio.AbstractEventLoop] = None):
        super().__init__()
        self.value_stream = Event.Event()
        self.__input_stream = input_stream.add_ref()
        self.__sample_value = SampleValue()
        self.__listener = input_stream.value_stream.listen(self.__value_changed)
        self.__sample_value.value = input_stream.value

        async def sample_loop(period: float, value_stream: Event.Event, sample_value: SampleValue) -> None:
            while True:
                await asyncio.sleep(period)
                if sample_value.is_dirty:
                    sample_value.value = sample_value.pending_value
                    sample_value.is_dirty = False
                    value_stream.fire(sample_value.value)

        self.__sample_task = StreamTask(sample_loop(period, self.value_stream, self.__sample_value))

    def about_to_delete(self) -> None:
        self.__listener.close()
        self.__listener = None
        self.__input_stream.remove_ref()
        self.__input_stream = None
        self.__sample_task.clear()
        self.__sample_task = typing.cast(StreamTask, None)
        super().about_to_delete()

    def __value_changed(self, value):
        self.__sample_value.set_pending_value(value)

    @property
    def value(self):
        return self.__sample_value.value


ConstantStreamT = typing.TypeVar('ConstantStreamT')

class ConstantStream(AbstractStream[ConstantStreamT]):

    def __init__(self, value: ConstantStreamT):
        super().__init__()
        self.__value = value
        self.value_stream = Event.Event()

    def about_to_delete(self) -> None:
        self.__value = typing.cast(ConstantStreamT, None)
        super().about_to_delete()

    @property
    def value(self) -> ConstantStreamT:
        return self.__value


PropertyChangedEventStreamT = typing.TypeVar('PropertyChangedEventStreamT')

class PropertyChangedEventStream(AbstractStream):
    """A stream generated from observing a property changed event of an Observable object."""

    # see https://rehansaeed.com/reactive-extensions-part2-wrapping-events/

    def __init__(self, source_object: typing.Union[Observable.Observable, AbstractStream[Observable.Observable]], property_name: str, cmp=None):
        super().__init__()
        # outgoing messages
        self.value_stream = Event.Event()
        # references
        if not isinstance(source_object, AbstractStream):
            source_object = ConstantStream(source_object)
        self.__source_stream = typing.cast(AbstractStream, source_object.add_ref())
        self.__source_object = None
        # initialize
        self.__property_name = property_name
        self.__value = None
        self.__cmp = cmp if cmp else operator.eq
        self.__property_changed_listener = None
        # listen for stream changes
        def source_object_changed(source_object: typing.Optional[Observable.Observable]) -> None:
            if self.__property_changed_listener:
                self.__property_changed_listener.close()
                self.__property_changed_listener = None
            self.__source_object = source_object
            if self.__source_object:
                self.__property_changed_listener = self.__source_object.property_changed_event.listen(self.__property_changed)
            self.__property_changed(property_name)
        self.__source_stream_listener = self.__source_stream.value_stream.listen(source_object_changed)
        source_object_changed(self.__source_stream.value)

    def about_to_delete(self) -> None:
        if self.__property_changed_listener:
            self.__property_changed_listener.close()
            self.__property_changed_listener = None
        self.__source_stream_listener.close()
        self.__source_stream_listener = None
        self.__source_stream.remove_ref()
        self.__source_stream = typing.cast(AbstractStream, None)
        super().about_to_delete()

    @property
    def value(self):
        return self.__value

    def __property_changed(self, key):
        if key == self.__property_name:
            new_value = getattr(self.__source_object, self.__property_name, None)
            if not self.__cmp(new_value, self.__value):
                self.__value = new_value
                self.value_stream.fire(self.__value)


class ConcatStream(AbstractStream):
    """Make a new stream for each new value of input stream and concatenate new stream output."""

    def __init__(self, stream: AbstractStream, concat_fn):
        super().__init__()
        # outgoing messages
        self.value_stream = Event.Event()
        # references
        self.__stream = stream.add_ref()
        # initialize
        self.__concat_fn = concat_fn
        self.__value = None
        self.__out_stream = None
        self.__out_stream_listener = None
        # listen for stream changes
        self.__stream_listener = stream.value_stream.listen(self.__stream_changed)
        self.__stream_changed(stream.value)

    def about_to_delete(self) -> None:
        if self.__out_stream:
            self.__out_stream_listener.close()
            self.__out_stream_listener = None
            self.__out_stream.remove_ref()
            self.__out_stream = None
        self.__value = None
        self.__stream_listener.close()
        self.__stream_listener = None
        self.__stream.remove_ref()
        self.__stream = None
        super().about_to_delete()

    @property
    def value(self):
        return self.__value

    def __stream_changed(self, item):
        if self.__out_stream:
            self.__out_stream_listener.close()
            self.__out_stream_listener = None
            self.__out_stream.remove_ref()
            self.__out_stream = None
        if item:
            def out_stream_changed(new_value):
                self.__value = new_value
                self.value_stream.fire(new_value)
            self.__out_stream = self.__concat_fn(item)
            self.__out_stream.add_ref()
            self.__out_stream_listener = self.__out_stream.value_stream.listen(out_stream_changed)
            out_stream_changed(self.__out_stream.value)
        else:
            self.__value = None
            self.value_stream.fire(None)


class OptionalStream(AbstractStream):
    """Sends value from input stream or None."""

    def __init__(self, stream: AbstractStream, pred: typing.Callable[[typing.Any], bool]):
        super().__init__()
        self.__stream = stream.add_ref()
        self.__pred = pred
        self.__stream_listener = self.__stream.value_stream.listen(self.__value_changed)
        self.value_stream = Event.Event()
        self.__value_changed(self.__stream.value)

    def about_to_delete(self) -> None:
        self.__stream_listener.close()
        self.__stream_listener = None
        self.__stream.remove_ref()
        self.__stream = None
        super().about_to_delete()

    @property
    def value(self):
        return None

    def __value_changed(self, value) -> None:
        if self.__pred(value):
            self.value_stream.fire(value)
        else:
            self.value_stream.fire(None)


class PrintStream(ReferenceCounting.ReferenceCounted):
    """Prints value from input stream."""

    def __init__(self, stream: AbstractStream):
        super().__init__()
        self.__stream = stream.add_ref()
        self.__stream_listener = self.__stream.value_stream.listen(self.__value_changed)

    def about_to_delete(self) -> None:
        self.__stream_listener.close()
        self.__stream_listener = None
        self.__stream.remove_ref()
        self.__stream = None
        super().about_to_delete()

    def __value_changed(self, value) -> None:
        print(f"value={value}")


class ValueStreamAction:
    """Calls an action function when the stream value changes."""

    def __init__(self, stream: AbstractStream, fn: typing.Callable[[typing.Any], None]):
        super().__init__()
        self.__stream = stream.add_ref()
        self.__stream_listener = self.__stream.value_stream.listen(self.__value_changed)
        self.__fn = fn

    def close(self) -> None:
        self.__stream_listener.close()
        self.__stream_listener = None
        self.__stream.remove_ref()
        self.__stream = None
        self.__fn = typing.cast(typing.Callable[[typing.Any], None], None)

    def __value_changed(self, value) -> None:
        self.__fn(value)


class ValueChangeType(enum.IntEnum):
    BEGIN = 0
    CHANGE = 1
    END = 2


class ValueChange(typing.Generic[T]):
    def __init__(self, state: int, value: T):
        self.state = state
        self.value = value

    @property
    def is_begin(self) -> bool:
        return self.state == ValueChangeType.BEGIN

    @property
    def is_end(self) -> bool:
        return self.state == ValueChangeType.END


class ValueChangeStream(ValueStream[ValueChange[T]]):
    def __init__(self, value_stream: AbstractStream[T]):
        super().__init__()
        self.__value_stream = value_stream.add_ref()
        self.__value_stream_listener = self.__value_stream.value_stream.listen(self.__value_changed)
        self.__is_active = False

    def about_to_delete(self) -> None:
        self.__value_stream_listener.close()
        self.__value_stream_listener = None
        self.__value_stream.remove_ref()
        self.__value_stream = None
        super().about_to_delete()

    def _send_value(self) -> None:
        if self.__is_active:
            assert self.value is not None
            super()._send_value()

    def begin(self) -> None:
        self.__is_active = True
        self.value = ValueChange(ValueChangeType.BEGIN, self.__value_stream.value)

    def end(self) -> None:
        self.value = ValueChange(ValueChangeType.END, self.__value_stream.value)
        self.__is_active = False

    def __value_changed(self, value: typing.Optional[T]) -> None:
        self.value = ValueChange(ValueChangeType.CHANGE, self.__value_stream.value)


class ValueChangeStreamReactor:
    def __init__(self, value_change_stream: ValueChangeStream):
        self.__value_change_stream = value_change_stream.add_ref()
        self.__value_changed_listener = value_change_stream.value_stream.listen(self.__value_changed)
        self.__event_queue: asyncio.Queue = asyncio.Queue()
        self.__task: typing.Optional[asyncio.Task] = None

    def close(self) -> None:
        if self.__task:
            self.__task.cancel()
            self.__task = None
        self.__value_changed_listener.close()
        self.__value_changed_listener = None
        self.__value_change_stream.remove_ref()
        self.__value_change_stream = None

    def __value_changed(self, value_change: ValueChange[float]) -> None:
        self.__event_queue.put_nowait(value_change)

    def run(self, cfn: typing.Callable[[ValueChangeStreamReactor], typing.Coroutine]) -> None:
        assert not self.__task
        self.__task = asyncio.get_event_loop().create_task(cfn(self))

    async def begin(self) -> None:
        while True:
            value_change = await self.__event_queue.get()
            if value_change.state == ValueChangeType.BEGIN:
                break

    async def next_value_change(self) -> ValueChange:
        return await self.__event_queue.get()

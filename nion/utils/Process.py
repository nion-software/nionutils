"""
Utility classes for implementing task queues and sets.
"""

from __future__ import annotations

# standard libraries
import asyncio
import contextlib
import copy
import dataclasses
import datetime
import queue
import threading
import time
import typing

# third party libraries
# None

# local libraries
# None


class TaskQueue:
    def __init__(self) -> None:
        # Python 3.9+: use queue.Queue[typing.Callable[[], None]]
        self.__queue: typing.Any = queue.Queue()

    def put(self, task: typing.Callable[[], None]) -> None:
        self.__queue.put(task)

    def perform_tasks(self) -> None:
        # perform any pending operations
        qsize = self.__queue.qsize()
        while not self.__queue.empty() and qsize > 0:
            try:
                task = self.__queue.get(False)
            except queue.Empty:
                pass
            else:
                with audit(f"taskqueue.{task}"):
                    task()
                self.__queue.task_done()
            qsize -= 1

    def clear_tasks(self) -> None:
        # perform any pending operations
        qsize = self.__queue.qsize()
        while not self.__queue.empty() and qsize > 0:
            try:
                task = self.__queue.get(False)
            except queue.Empty:
                pass
            else:
                self.__queue.task_done()
            qsize -= 1


# keeps a set of tasks to do when perform_tasks is called.
# each task is associated with a key. overwriting a key
# will discard any task currently associated with that key.
class TaskSet:
    def __init__(self) -> None:
        self.__task_dict: typing.Dict[str, typing.Callable[[], None]] = dict()
        self.__task_dict_mutex = threading.RLock()

    def add_task(self, key: str, task: typing.Callable[[], None]) -> None:
        with self.__task_dict_mutex:
            self.__task_dict[key] = task

    def clear_task(self, key: str) -> None:
        with self.__task_dict_mutex:
            if key in self.__task_dict:
                self.__task_dict.pop(key, None)

    def perform_tasks(self) -> None:
        with self.__task_dict_mutex:
            task_dict = copy.copy(self.__task_dict)
            self.__task_dict.clear()
        for task in task_dict.values():
            with audit(f"taskset.{task}"):
                task()


def sync_event_loop(event_loop: typing.Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Synchronize the event loop, ensuring all tasks are complete.

    Uses the current event loop if event_loop is None.
    """
    event_loop = event_loop or asyncio.get_running_loop()
    # give event loop one chance to finish up
    event_loop.stop()
    event_loop.run_forever()
    # wait for everything to finish, including tasks running in executors
    # this assumes that all outstanding tasks finish in a reasonable time (i.e. no infinite loops).
    tasks = asyncio.all_tasks(loop=event_loop)
    if tasks:
        for task in tasks:
            task.cancel()
        gather_future = asyncio.gather(*tasks, return_exceptions=True)
    else:
        # work around bad design in gather (always uses global event loop in Python 3.8)
        gather_future = event_loop.create_future()
        gather_future.set_result([])
    event_loop.run_until_complete(gather_future)


def close_event_loop(event_loop: typing.Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Synchronize and optionally close the event loop.

    If a specific event loop is passed, it will be closed. Otherwise only synchronized.
    """
    sync_event_loop(event_loop)
    if event_loop:
        # due to a bug in Python libraries, the default executor needs to be shutdown explicitly before the event loop
        # see http://bugs.python.org/issue28464 . this bug manifests itself in at least one way: an intermittent failure
        # in test_document_controller_releases_itself. reproduce by running the contents of that test in a loop of 100.
        _default_executor = getattr(event_loop, "_default_executor", None)
        if _default_executor:
            _default_executor.shutdown()
        event_loop.close()


@dataclasses.dataclass
class AuditEvent:
    audit_index: int
    audit_id: str
    is_active: bool
    start: float
    end: float
    thread: threading.Thread
    parent: typing.Optional[AuditEvent]


class Audit:
    _index = 0

    def __init__(self) -> None:
        self.__audit_state: typing.Dict[int, AuditEvent] = dict()
        self.__audit_stacks: typing.Dict[threading.Thread, typing.List[AuditEvent]] = dict()
        self.__audit_context_mutex = threading.RLock()

    def clear(self) -> None:
        with self.__audit_context_mutex:
            for audit_index, audit_event in list(self.__audit_state.items()):
                if not audit_event.is_active:
                    del self.__audit_state[audit_index]

    def enter(self, audit_id: str) -> int:
        with self.__audit_context_mutex:
            audit_index = Audit._index
            Audit._index += 1
            audit_stack = self.__audit_stacks.get(threading.current_thread(), None)
            parent_audit_event = audit_stack[-1] if audit_stack else None
            audit_event = AuditEvent(audit_index, audit_id, True, time.perf_counter_ns(), 0, threading.current_thread(), parent_audit_event)
            self.__audit_state[audit_index] = audit_event
            self.__audit_stacks.setdefault(threading.current_thread(), []).append(audit_event)
            return audit_index

    def exit(self, audit_index: int) -> None:
        with self.__audit_context_mutex:
            self.__audit_stacks[threading.current_thread()].pop(-1)
            audit_event = self.__audit_state[audit_index]
            audit_event.end = time.perf_counter_ns()
            audit_event.is_active = False

    def report(self, threshold: float = 100e-6) -> None:
        print(f"-------------- Audit report: {datetime.datetime.now()}")
        with self.__audit_context_mutex:
            audit_events = list(self.__audit_state.values())
        audit_events.sort(key=lambda audit_event: audit_event.start)

        def print_audit_event(audit_event: AuditEvent, indent: str) -> None:
            if audit_event.end:
                if (audit_event.end - audit_event.start) / 1e9 > threshold:
                    print(f"{indent}{audit_event.audit_id}: {(audit_event.end - audit_event.start) / 1000}us")
            else:
                print(f"{indent}{audit_event.audit_id}: active")
            for child_audit_event in audit_events:
                if child_audit_event.parent == audit_event:
                    print_audit_event(child_audit_event, indent + "..")

        index = 0
        for audit_event in audit_events:
            if not audit_event.parent:
                index += 1
                print(f"{index}: thread {audit_event.thread}")
                print_audit_event(audit_event, "..")


_audit = Audit()
_audit_enabled = False


@contextlib.contextmanager
def audit(audit_id: str) -> typing.Iterator[typing.Any]:
    if _audit_enabled:
        audit_index = _audit.enter(audit_id)
        try:
            yield
        finally:
           _audit.exit(audit_index)
    else:
        yield


def audited(fn: typing.Callable[[], None], audit_id: str) -> typing.Callable[[], None]:
    def audited_fn() -> None:
        with audit(audit_id):
            fn()
    return audited_fn

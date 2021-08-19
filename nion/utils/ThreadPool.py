"""
Useful classes for handling threads.
"""

# standard libraries
import concurrent.futures
import copy
import dataclasses
import logging
import queue
import threading
import time
import typing
import weakref

# third party libraries
# None

# local libraries
# None


class ThreadDispatcher(object):

    """
        Invoke fn when trigger is called. Minimum interval
        limits how often the fn will be invoked.
    """

    def __init__(self, fn, minimum_interval=0.001):
        self.__fn = fn
        self.__thread_break = False
        self.__thread_event = threading.Event()
        self.__triggered_event = threading.Event()
        self.__thread_lock = threading.Lock()
        self.__thread = threading.Thread(target=self.__process)
        self.__thread.daemon = True
        self.__minimum_interval = minimum_interval
        self.__last_time = 0

    def start(self):
        self.__thread.start()

    def close(self):
        with self.__thread_lock:
            self.__thread_break = True
            self.__thread_event.set()
        self.__thread.join()
        self.__thread = None
        self.__fn = None

    def trigger(self, wait=False):
        if wait:
            with self.__thread_lock:
                self.__triggered_event.clear()
                self.__thread_event.set()
            self.__triggered_event.wait()
        else:
            self.__thread_event.set()

    def __process(self):
        while True:
            self.__thread_event.wait()
            with self.__thread_lock:
                self.__thread_event.clear()  # put this inside lock to avoid race condition
            if self.__thread_break:
                break
            thread_event_set = False
            while not self.__thread_break:
                elapsed = time.time() - self.__last_time
                if self.__minimum_interval and elapsed < self.__minimum_interval:
                    if self.__thread_event.wait(self.__minimum_interval - elapsed):
                        thread_event_set = True  # set this so that we know to set it after this loop
                    self.__thread_event.clear()  # clear this so that it doesn't immediately trigger again
                else:
                    break
            if thread_event_set:
                self.__thread_event.set()
            if self.__thread_break:
                break
            try:
                self.__fn()
                self.__triggered_event.set()
            except Exception as e:
                import traceback
                logging.debug("Processing thread exception %s", e)
                traceback.print_exc()
                traceback.print_stack()
            self.__last_time = time.time()


class ThreadPoolTask(object):
    """
        Execute a task once. The task may be canceled but if it is already
        in progress, canceling will wait until it finishes.
    """

    def __init__(self, fn, finished_fn, description):
        self.__description = description if description else str()
        self.__fn = fn
        self.__finished_fn = finished_fn
        self.__lock = threading.RLock()

    def cancel(self):
        #logging.debug("Task cancel - %s", self)
        with self.__lock:
            #logging.debug("Task cancel + %s", self)
            if self.__fn:
                self.__fn = None
                self.__finished_fn(self)

    def execute(self):
        # logging.debug("Task execute - %s %s", self, self.__description)
        with self.__lock:
            # logging.debug("Task execute + %s", self)
            if self.__fn:
                try:
                    self.__fn()
                except Exception as e:
                    import traceback
                    logging.debug("Task thread exception %s", e)
                    traceback.print_exc()
                    traceback.print_stack()
                self.__fn = None
                self.__finished_fn(self)
            # logging.debug("Task execute ++ %s", self)


class ThreadPool(object):

    def __init__(self):
        self.__closed = False
        self.__queue = queue.Queue()
        self.__threads = list()
        self.__lock = threading.RLock()
        self.__tasks = list()

    def close(self):
        with self.__lock:
            self.__closed = True
            tasks = copy.copy(self.__tasks)
        for task in tasks:
            task.cancel()
        for _ in self.__threads:
            self.__queue.put(None)
        if len(self.__threads) > 0:
            self.__queue.join()

    def start(self, thread_count=16):
        for _ in range(thread_count):
            thread = threading.Thread(target=self.__run)
            thread.daemon = True
            thread.start()
            self.__threads.append(thread)

    def queue_fn(self, fn, description=None):
        with self.__lock:
            if not self.__closed:
                def remove_task(task):
                    with self.__lock:
                        self.__tasks.remove(task)
                task = ThreadPoolTask(fn, remove_task, description)
                self.__tasks.append(task)
                self.__queue.put(task)

    def __run(self):
        while True:
            task = self.__queue.get()
            if task and not self.__closed:
                task.execute()
            self.__queue.task_done()
            if not task:
                break

    def run_all(self):
        while not self.__queue.empty():
            task = self.__queue.get()
            if task and not self.__closed:
                task.execute()
            self.__queue.task_done()
            if not task:
                break

    def run_one(self):
        if not self.__queue.empty():
            task = self.__queue.get()
            if task and not self.__closed:
                task.execute()
            self.__queue.task_done()


@dataclasses.dataclass
class DispatcherInfo:
    is_dispatching_lock: threading.RLock
    is_dispatch_pending: bool
    dispatch_future: typing.Optional[concurrent.futures.Future]
    dispatch_thread_cancel: threading.Event
    cached_value_time: float


class SingleItemDispatcher:
    """Dispatch a function to the thread pool, ensuring only one is running at once."""
    def __init__(self, *, executor: typing.Optional[concurrent.futures.ThreadPoolExecutor] = None, minimum_period: float = 0.0):
        self.__executor = executor or concurrent.futures.ThreadPoolExecutor()
        self.__minimum_period = minimum_period
        self.__dispatcher_info = DispatcherInfo(threading.RLock(), False, None, threading.Event(), 0.0)

        def finalize(dispatcher_info: DispatcherInfo, s: str) -> None:
            recompute_future = dispatcher_info.dispatch_future  # avoid race by using local
            if recompute_future:
                dispatcher_info.dispatch_thread_cancel.set()
                concurrent.futures.wait([recompute_future])

        weakref.finalize(self, finalize, self.__dispatcher_info, str(self))

    def close(self) -> None:
        pass

    def dispatch(self, fn: typing.Callable[[], None]) -> concurrent.futures.Future:
        # dispatch the function on a thread.
        # if already executing, ensure the thread dispatch again.
        # may be called on the main thread or a thread - must return quickly in both cases.
        with self.__dispatcher_info.is_dispatching_lock:
            # in case thread is already running, set pending.
            # the only way the thread can end is if not pending within lock.
            # dispatch_future can only be set within lock.
            self.__dispatcher_info.is_dispatch_pending = True
            if not self.__dispatcher_info.dispatch_future:

                def dispatch_task(fn: typing.Callable[[], None], minimum_time: float, dispatcher_info: DispatcherInfo) -> None:
                    while True:
                        try:
                            if dispatcher_info.dispatch_thread_cancel.wait(0.05):  # gather changes and helps tests run faster
                                return
                            current_time = time.time()
                            if current_time < dispatcher_info.cached_value_time + minimum_time:
                                if dispatcher_info.dispatch_thread_cancel.wait(dispatcher_info.cached_value_time + minimum_time - current_time):
                                    return
                            dispatcher_info.is_dispatch_pending = False  # any pending calls up to this point will be realized in the recompute
                            fn()
                            dispatcher_info.cached_value_time = time.time()
                        finally:
                            with dispatcher_info.is_dispatching_lock:
                                # the only way the thread can end is if not pending within lock.
                                # recompute_future can only be set within lock.
                                if not dispatcher_info.is_dispatch_pending:
                                    dispatcher_info.dispatch_future = None
                                    break

                self.__dispatcher_info.dispatch_future = self.__executor.submit(dispatch_task, fn, self.__minimum_period, self.__dispatcher_info)
            return self.__dispatcher_info.dispatch_future

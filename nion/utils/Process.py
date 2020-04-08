"""
Utility classes for implementing task queues and sets.
"""

# standard libraries
import asyncio
import copy
import queue
import threading

# third party libraries
# None

# local libraries
# None


class TaskQueue(queue.Queue):

    def perform_tasks(self):
        # perform any pending operations
        qsize = self.qsize()
        while not self.empty() and qsize > 0:
            try:
                task = self.get(False)
            except queue.Empty:
                pass
            else:
                task()
                self.task_done()
            qsize -= 1

    def clear_tasks(self):
        # perform any pending operations
        qsize = self.qsize()
        while not self.empty() and qsize > 0:
            try:
                task = self.get(False)
            except queue.Empty:
                pass
            else:
                self.task_done()
            qsize -= 1


# keeps a set of tasks to do when perform_tasks is called.
# each task is associated with a key. overwriting a key
# will discard any task currently associated with that key.
class TaskSet(object):
    def __init__(self):
        self.__task_dict = dict()
        self.__task_dict_mutex = threading.RLock()
    def add_task(self, key, task):
        with self.__task_dict_mutex:
            self.__task_dict[key] = task
    def clear_task(self, key):
        with self.__task_dict_mutex:
            if key in self.__task_dict:
                self.__task_dict.pop(key, None)
    def perform_tasks(self):
        with self.__task_dict_mutex:
            task_dict = copy.copy(self.__task_dict)
            self.__task_dict.clear()
        for task in task_dict.values():
            task()


def close_event_loop(event_loop: asyncio.AbstractEventLoop) -> None:
    # give event loop one chance to finish up
    event_loop.stop()
    event_loop.run_forever()
    # wait for everything to finish, including tasks running in executors
    # this assumes that all outstanding tasks finish in a reasonable time (i.e. no infinite loops).
    all_tasks_fn = getattr(asyncio, "all_tasks", None)
    if not all_tasks_fn:
        all_tasks_fn = asyncio.Task.all_tasks
    tasks = all_tasks_fn(loop=event_loop)
    if tasks:
        gather_future = asyncio.gather(*tasks, return_exceptions=True)
    else:
        # work around bad design in gather (always uses global event loop in Python 3.8)
        gather_future = event_loop.create_future()
        gather_future.set_result([])
    event_loop.run_until_complete(gather_future)
    # due to a bug in Python libraries, the default executor needs to be shutdown explicitly before the event loop
    # see http://bugs.python.org/issue28464 . this bug manifests itself in at least one way: an intermittent failure
    # in test_document_controller_releases_itself. reproduce by running the contents of that test in a loop of 100.
    _default_executor = getattr(event_loop, "_default_executor", None)
    if _default_executor:
        _default_executor.shutdown()
    event_loop.close()

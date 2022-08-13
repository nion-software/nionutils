"""
An event object to which to attach listeners.
"""

from __future__ import annotations

# standard libraries
import datetime
import threading
import sys
import time

# third party libraries
# None

# local libraries
# None


last_time: float = 0.0
last_time_lock = threading.RLock()


def utcnow() -> datetime.datetime:
    global last_time
    # windows utcnow has a resolution of 1ms, need to handle specially.
    if sys.platform == "win32":
        # see https://www.python.org/dev/peps/pep-0564/#annex-clocks-resolution-in-python
        with last_time_lock:
            current_time = int(time.time_ns() / 1E3) / 1E6  # truncate to microseconds, convert to seconds
            while current_time <= last_time:
                current_time += 0.000001
            last_time = current_time
        utcnow = datetime.datetime.utcfromtimestamp(current_time)
    else:
        utcnow = datetime.datetime.utcnow()
    return utcnow


def now() -> datetime.datetime:
    return datetime.datetime.now()

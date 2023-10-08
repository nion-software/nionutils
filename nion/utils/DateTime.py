"""
An event object to which to attach listeners.
"""

from __future__ import annotations

# standard libraries
import datetime
import threading
import sys
import time
import typing

# third party libraries
# None

# local libraries
# None


last_time: float = 0.0
last_time_lock = threading.RLock()


class DateTimeUTC:
    def __init__(self, timestamp: typing.Optional[typing.Union[datetime.datetime, DateTimeUTC]] = None) -> None:
        if isinstance(timestamp, DateTimeUTC):
            self.__timestamp = timestamp.timestamp
        elif isinstance(timestamp, datetime.datetime):
            if timestamp.tzinfo is not None and timestamp.tzinfo.utcoffset(timestamp) is not None:
                self.__timestamp = timestamp.astimezone(datetime.timezone.utc)
            else:
                self.__timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
        else:
            global last_time
            # windows utcnow has a resolution of 1ms, need to handle specially.
            if sys.platform == "win32":
                # see https://www.python.org/dev/peps/pep-0564/#annex-clocks-resolution-in-python
                with last_time_lock:
                    current_time = int(time.time_ns() / 1E3) / 1E6  # truncate to microseconds, convert to seconds
                    while current_time <= last_time:
                        current_time += 0.000001
                    last_time = current_time
                timestamp = datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc)
            else:
                timestamp = datetime.datetime.now(datetime.timezone.utc)
            self.__timestamp = timestamp
        assert self.__timestamp.tzinfo == datetime.timezone.utc

    @property
    def timestamp_naive(self) -> datetime.datetime:
        return self.__timestamp.replace(tzinfo=None)

    @property
    def timestamp(self) -> datetime.datetime:
        return self.__timestamp


def utcnow() -> datetime.datetime:
    return DateTimeUTC().timestamp_naive


def now() -> datetime.datetime:
    return datetime.datetime.now()

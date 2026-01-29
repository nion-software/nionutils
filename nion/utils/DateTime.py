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
FILETIME_TICKS_PER_MICROSECOND = 10 # Hundreds of nanoseconds in a microsecond
FILETIME_TICKS_PER_SECOND = 10000000  # Hundreds of nanoseconds (0.1 microseconds) in a second
FILETIME_EPOCH = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)


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

def get_datetime_from_filetime(filetime: int) -> datetime.datetime:
    """Converts a windows filetime to a datetime in UTC
    Windows file time is: the time in hundreds of nanoseconds since January 1st 1601 UTC
    Since datetime objects only have 1 microsecond precision the exact filetime is not fully preserved.
    """
    try:
        total_microseconds = filetime // FILETIME_TICKS_PER_MICROSECOND # Integer division is required to prevent floating point errors
        return FILETIME_EPOCH + datetime.timedelta(microseconds=total_microseconds)
    except OverflowError:
        if filetime < 0:
            return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        else:
            return datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)


def get_filetime_from_datetime(time_dt: datetime.datetime) -> int:
    """ Converts a datetime to a Windows file time.
    If the datetime's timezone is None it is assumed to be UTC.
    """
    if time_dt.tzinfo is None:
        time_dt = time_dt.replace(tzinfo=datetime.timezone.utc)

    delta = time_dt.astimezone(datetime.timezone.utc) - FILETIME_EPOCH
    file_time_ticks = (delta.days * 24 * 3600 + delta.seconds) * FILETIME_TICKS_PER_SECOND + delta.microseconds * FILETIME_TICKS_PER_MICROSECOND
    return file_time_ticks
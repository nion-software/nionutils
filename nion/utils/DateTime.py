"""
An event object to which to attach listeners.
"""

from __future__ import annotations

# standard libraries
import datetime
import threading
import typing

# third party libraries
# None

# local libraries
# None


# the last timestamp which DateTimeUTC created for the current time. the lock protects it.
_last_timestamp = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
_last_timestamp_lock = threading.Lock()

# a clock which reads this far before the last timestamp has been set back.
_CLOCK_SET_BACK_THRESHOLD = datetime.timedelta(milliseconds=1)

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
            global _last_timestamp
            # a timestamp for the current time is later than every earlier one. it waits for the clock to pass the last
            # timestamp, so that it does not run ahead of the clock. after the clock is set back, waiting would last as
            # long as the clock went back, so the timestamp continues from the last one instead.
            with _last_timestamp_lock:
                timestamp = datetime.datetime.now(datetime.timezone.utc)
                if _last_timestamp - timestamp >= _CLOCK_SET_BACK_THRESHOLD:
                    timestamp = _last_timestamp + datetime.timedelta(microseconds=1)
                while timestamp <= _last_timestamp:
                    timestamp = datetime.datetime.now(datetime.timezone.utc)
                _last_timestamp = timestamp
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


def get_datetime_from_windows_filetime(filetime: int) -> datetime.datetime:
    """Converts a windows filetime to a datetime in UTC

    Windows file time is: the time in hundreds of nanoseconds since January 1st 1601 UTC
    Since datetime objects only have 1 microsecond precision the exact filetime is not fully preserved.
    """
    try:
        total_microseconds, remainder = divmod(filetime, FILETIME_TICKS_PER_MICROSECOND)  # regular division would introduce floating point issues
        total_microseconds += 0 if remainder < 5 else 1  # we can manually do rounding to avoid the floating point issues
        return FILETIME_EPOCH + datetime.timedelta(microseconds=total_microseconds)
    except OverflowError:
        if filetime < 0:
            return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        else:
            return datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)


def get_windows_filetime_from_datetime(time_dt: datetime.datetime) -> int:
    """Converts a datetime to a Windows file time.

    If the datetime's timezone is None it is assumed to be UTC.
    """
    if time_dt.tzinfo is None:
        time_dt = time_dt.replace(tzinfo=datetime.timezone.utc)

    delta = time_dt.astimezone(datetime.timezone.utc) - FILETIME_EPOCH
    file_time_ticks = (delta.days * 24 * 3600 + delta.seconds) * FILETIME_TICKS_PER_SECOND + delta.microseconds * FILETIME_TICKS_PER_MICROSECOND
    return file_time_ticks

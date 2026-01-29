import unittest
import datetime
from nion.utils import DateTime

class Test(unittest.TestCase):
    def test_datetime_to_filetime(self) -> None:
        test_datetimes = [
            (datetime.datetime(2025, 1, 1), 133801632000000000),
            (datetime.datetime(2025, 1, 1, 12, 30, 45), 133802082450000000),
            (datetime.datetime(2025, 12, 31, 23, 59, 59, 999999), 134116991999999990),  # max microsecond
            (datetime.datetime(1970, 1, 1, 0, 0, 0), 116444736000000000),  # Unix epoch
            (datetime.datetime(9999, 12, 31, 23, 59, 59, 999999), 2650467743999999990),  # Python max datetime.datetime
            (datetime.datetime(2024, 2, 29, 15, 0), 133536924000000000), # leap day
            (datetime.datetime(2000, 2, 29, 23, 59, 59), 125963423990000000), # leap year divisible by 400
            (datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone.utc),  133932528000000000),# UTC aware
            (datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30))),133932330000000000), # India Standard Time
            (datetime.datetime(1950, 5, 17, 8, 20, 0, tzinfo=datetime.timezone.utc), 110251020000000000),  # negative time stamp
            (datetime.datetime(1066, 1, 1, 0, 0, 0), -168829920000000000),  # before windows filetime start
            (datetime.datetime(2025, 7, 15, 10, 5, 30, 123456), 133970475301234560), # microseconds
            (datetime.datetime(2025, 7, 15, 10, 5, 30, 0), 133970475300000000), # zero microseconds
            (datetime.datetime(2035, 8, 1, 9, 0, tzinfo=datetime.timezone.utc), 137140452000000000), # 10 years ahead
            (datetime.datetime(2100, 1, 1, 0, 0, 0),157469184000000000),  # non‑leap century year
            (datetime.datetime(2025, 3, 30, 0, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=-1))), 133877718000000000),  # before daylight savings
            (datetime.datetime(2025, 3, 30, 1, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=0))), 133877718000000000),  # ambiguous transition
            (datetime.datetime(2025, 10, 26, 1, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=0))), 134059158000000000),  # repeated hour
            (datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=4))), 133932384000000000),  # US Eastern
            (datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=9))), 133932204000000000),  # Japan time
        ]
        for datetime_in, expected_filetime in test_datetimes:
            with self.subTest(f"Datetime to filetime {datetime_in.isoformat()} expects {expected_filetime}"):
                filetime = DateTime.get_filetime_from_datetime(datetime_in)
                print(filetime)
                self.assertEqual(filetime, expected_filetime)
                datetime_out = DateTime.get_datetime_from_filetime(filetime)
                if datetime_in.tzinfo is None:

                    time_in_utc = datetime_in.replace(tzinfo=datetime.timezone.utc)
                else:
                    time_in_utc = datetime_in.astimezone(tz=datetime.timezone.utc)
                self.assertEqual(time_in_utc, datetime_out)

            with self.subTest(f"Filetime to datetime {datetime_in} expects {expected_filetime}"):
                datetime_out = DateTime.get_datetime_from_filetime(expected_filetime)
                if datetime_in.tzinfo is None:

                    time_in_utc = datetime_in.replace(tzinfo=datetime.timezone.utc)
                else:
                    time_in_utc = datetime_in.astimezone(tz=datetime.timezone.utc)
                self.assertEqual(time_in_utc, datetime_out)
                filetime_out = DateTime.get_filetime_from_datetime(datetime_out)
                self.assertEqual(filetime_out, expected_filetime)

    def test_invalid_times(self) -> None:
        test_filetimes = [
            (datetime.datetime.max, 2650467744999999990), # Above the max datetime
            (datetime.datetime.max, 9223372036854775807), # Int max,
            (datetime.datetime.min, -9223372036854775808), # int min
        ]
        for i, (expected_datetime, filetime_in) in enumerate(test_filetimes):
            with self.subTest(f"Invalid filetime test: {expected_datetime} expects {filetime_in}"):
                datetime_out = DateTime.get_datetime_from_filetime(filetime_in)
                if expected_datetime.tzinfo is None:

                    time_in_utc = expected_datetime.replace(tzinfo=datetime.timezone.utc)
                else:
                    time_in_utc = expected_datetime.astimezone(tz=datetime.timezone.utc)
                self.assertEqual(datetime_out, time_in_utc)

if __name__ == '__main__':
    unittest.main()

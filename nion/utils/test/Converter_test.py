# standard libraries
import datetime
import logging
import unittest

# local libraries
from nion.utils import Converter


class TestConverter(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_float_to_scaled_integer_with_negative_min(self) -> None:
        converter = Converter.FloatToScaledIntegerConverter(1000, -100, 100)
        self.assertAlmostEqual(converter.convert(0) or 0, 500)
        self.assertAlmostEqual(converter.convert(-100) or 0, 0)
        self.assertAlmostEqual(converter.convert(100) or 0, 1000)
        self.assertAlmostEqual(converter.convert_back(converter.convert(0)) or 0.0, 0)
        self.assertAlmostEqual(converter.convert_back(converter.convert(-100)) or 0.0, -100)
        self.assertAlmostEqual(converter.convert_back(converter.convert(100)) or 0.0, 100)
        # test case where min == max
        converter = Converter.FloatToScaledIntegerConverter(1000, 0, 0)
        self.assertAlmostEqual(converter.convert(0) or 0, 0)
        self.assertAlmostEqual(converter.convert_back(0) or 0.0, 0)
        # test case where min > max
        converter = Converter.FloatToScaledIntegerConverter(1000, 1, 0)
        self.assertAlmostEqual(converter.convert(0) or 0, 0)
        self.assertAlmostEqual(converter.convert_back(0) or 0.0, 0)

    def test_integer_to_string_converter(self) -> None:
        converter = Converter.IntegerToStringConverter()
        self.assertEqual(converter.convert_back("-1"), -1)
        self.assertEqual(converter.convert_back("2.45653"), 2)
        self.assertEqual(converter.convert_back("-adcv-2.15sa56aas"), -2)
        self.assertEqual(converter.convert_back("xx4."), 4)

    def test_date_to_string_converter(self) -> None:
        dt = datetime.datetime.utcnow()
        dt_str = dt.isoformat()
        # default converter
        converter = Converter.DatetimeToStringConverter()
        self.assertEqual(dt, converter.convert_back(converter.convert(dt)))
        self.assertEqual(dt_str, converter.convert(converter.convert_back(dt_str)))
        # local converter
        converter = Converter.DatetimeToStringConverter(is_local=True)
        self.assertEqual(dt, converter.convert_back(converter.convert(dt)))
        self.assertEqual(dt_str, converter.convert(converter.convert_back(dt_str)))
        # local+format converter
        format = "%Y-%m-%d %H:%M:%S"
        converter = Converter.DatetimeToStringConverter(is_local=True, format=format)
        self.assertEqual(dt.replace(microsecond=0), converter.convert_back(converter.convert(dt.replace(microsecond=0))))
        self.assertEqual(dt.strftime(format), converter.convert(converter.convert_back(dt.strftime(format))))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

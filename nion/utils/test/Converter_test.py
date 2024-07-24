# standard libraries
import logging
import typing
import unittest

# local libraries
from nion.utils import Converter
from nion.utils import DateTime


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
        dt = DateTime.utcnow()
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

    def test_tuple_to_value_converter(self) -> None:
        class TupleTestClass:
            __tuple = (10, 20, 30, 40)

            @property
            def tuple_property(self) -> tuple[typing.Any, ...]:
                return self.__tuple

            @tuple_property.setter
            def tuple_property(self, value: tuple[typing.Any, ...]) -> None:
                self.__tuple = value

        test_class = TupleTestClass()
        converter = Converter.TupleToValueConverter[int](test_class, "tuple_property", 2)
        self.assertEqual(converter.convert(test_class.tuple_property), 30)
        self.assertEqual(converter.convert_back(50), (10, 20, 50, 40))

    def test_tuple_of_integers_to_string_value_converter(self) -> None:
        class TupleTestClass:
            __tuple = (10, 20, 30, 40)

            @property
            def tuple_property(self) -> tuple[typing.Any, ...]:
                return self.__tuple

            @tuple_property.setter
            def tuple_property(self, value: tuple[typing.Any, ...]) -> None:
                self.__tuple = value

        test_class = TupleTestClass()
        converter = Converter.TupleOfIntegersToStringValueConverter(test_class, "tuple_property", 2)
        self.assertEqual(converter.convert(test_class.tuple_property), "30")
        self.assertEqual(converter.convert_back("50"), (10, 20, 50, 40))

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

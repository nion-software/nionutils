# standard libraries
import logging
import unittest

# third party libraries
# None

# local libraries
from nion.utils import Binding
from nion.utils import Event


class TupleModel:

    def __init__(self):
        self.__tuple = None
        self.property_changed_event = Event.Event()

    @property
    def tuple(self):
        return self.__tuple

    @tuple.setter
    def tuple(self, value):
        self.__tuple = value
        self.property_changed_event.fire("tuple")


class TestBindingClass(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_tuple_binding_pads_to_index_if_necessary(self):
        # this allows the source to more easily go from None to a partialy tuple None -> (3, None) -> (3, 4)
        source = TupleModel()
        self.assertEqual(None, source.tuple)
        binding0 = Binding.TuplePropertyBinding(source, "tuple", 0)
        binding2 = Binding.TuplePropertyBinding(source, "tuple", 2)
        binding0.update_source("abc")
        self.assertEqual(("abc", ), source.tuple)
        binding2.update_source("ghi")
        self.assertEqual(("abc", None, "ghi"), source.tuple)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

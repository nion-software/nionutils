# standard libraries
import logging
import unittest

# third party libraries
# None

# local libraries
from nion.utils import Binding
from nion.utils import Observable


class ListModel(Observable.Observable):

    def __init__(self):
        super().__init__()
        self.__items = list()

    def insert_item(self, index: int, value: str) -> None:
        self.__items.insert(index, value)
        self.notify_insert_item("items", value, index)

    def remove_item(self, index:int) -> None:
        value = self.__items[index]
        del self.__items[index]
        self.notify_remove_item("items", value, index)

    @property
    def items(self):
        return self.__items


class TestBindingClass(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_should_be_able_to_get_items_from_list_binding(self):
        list_model = ListModel()
        list_model.insert_item(0, "zero")
        list_model.insert_item(1, "one")
        list_model.insert_item(2, "two")
        binding = Binding.ListBinding(list_model, "items")
        items = binding.items
        self.assertEqual(len(items), 3)
        self.assertEqual(items[2], "two")
        list_model.insert_item(0, "negative")
        self.assertEqual(len(items), 4)
        self.assertEqual(items[3], "two")

    def test_inserting_and_removing_item_into_binding_notifies_target(self):
        list_model = ListModel()
        binding = Binding.ListBinding(list_model, "items")
        list_copy = list()

        def inserter(value: str, index: int) -> None:
            list_copy.insert(index, value)

        def remover(index: int) -> None:
            del list_copy[index]

        binding.inserter = inserter
        binding.remover = remover
        list_model.insert_item(0, "zero")
        list_model.insert_item(1, "one")
        self.assertEqual(len(list_copy), 2)
        self.assertEqual(list_copy[1], "one")
        list_model.remove_item(0)
        self.assertEqual(len(list_copy), 1)
        self.assertEqual(list_copy[0], "one")


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

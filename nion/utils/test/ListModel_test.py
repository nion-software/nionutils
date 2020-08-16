# standard libraries
import contextlib
import logging
import unittest

# third party libraries
# None

# local libraries
from nion.utils import ListModel
from nion.utils import Observable


class A:
    def __init__(self, s: str):
        self.s = s


class B:
    def __init__(self, a: A):
        self.s = a.s + "_B"


class TestListModelClass(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_filtered_list_is_sorted(self):
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l2 = ListModel.FilteredListModel(container=l, items_key="items")
        l2.sort_key = lambda x: x
        l2.mark_changed()
        self.assertEqual(["1", "2", "3", "4"], l2.items)
        l.remove_item(1)
        l.remove_item(1)
        self.assertEqual(["2", "3"], l2.items)
        l.insert_item(0, "5")
        l.insert_item(0, "1")
        self.assertEqual(["1", "2", "3", "5"], l2.items)

    def test_filtered_list_unsorted_retains_order(self):
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l2 = ListModel.FilteredListModel(container=l, items_key="items")
        l2.filter = ListModel.PredicateFilter(lambda x: x != "4")
        self.assertEqual(["3", "1", "2"], l2.items)
        l.remove_item(0)
        self.assertEqual(["1", "2"], l2.items)
        l.insert_item(0, "3")
        l.append_item("44")
        self.assertEqual(["3", "1", "2", "44"], l2.items)
        l2.begin_change()
        l.insert_item(0, "5")
        l.append_item("6")
        l2.end_change()
        self.assertEqual(["5", "3", "1", "2", "44", "6"], l2.items)

    def test_filtered_list_changing_from_sorted_to_unsorted_retains_order(self):
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l2 = ListModel.FilteredListModel(container=l, items_key="items")
        l2.sort_key = lambda x: x
        self.assertEqual(["1", "2", "3", "4"], l2.items)
        l2.filter = ListModel.PredicateFilter(lambda x: x != "4")
        l2.sort_key = None
        self.assertEqual(["3", "1", "2"], l2.items)
        l.remove_item(1)
        self.assertEqual(["3", "2"], l2.items)

    def test_filtered_list_changing_container_under_changes_retains_order(self):
        # the bug was that if list model is under a change and items are only
        # being rearranged (easy to occur with dependent list being sorted differently)
        # then there is no way to detect that it is not sorted anymore so it proceeds
        # as if it is already sorted properly.
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l2 = ListModel.ListModel("items")
        l2.append_item("4")
        l2.append_item("1")
        l2.append_item("2")
        l2.append_item("3")
        l3 = ListModel.FilteredListModel(container=l, items_key="items")
        self.assertEqual(["3", "1", "4", "2"], l3.items)
        l4 = ListModel.FilteredListModel(container=l3, items_key="items")
        self.assertEqual(["3", "1", "4", "2"], l4.items)
        l4.begin_change()
        l3.begin_change()
        l3.filter = ListModel.Filter(True)
        l3.end_change()
        l4.end_change()
        l4.begin_change()
        l3.begin_change()
        l3.container = l2
        l3.end_change()
        l4.end_change()
        self.assertEqual(["4", "1", "2", "3"], l3.items)
        self.assertEqual(["4", "1", "2", "3"], l4.items)

    def test_filtered_list_sends_begin_end_changes_for_single_insert_and_remove(self):
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l2 = ListModel.FilteredListModel(container=l, items_key="items")
        l2.sort_key = lambda x: x

        begin_changes_count = 0
        end_changes_count = 0

        def begin_changes(key):
            nonlocal begin_changes_count
            begin_changes_count += 1

        def end_changes(key):
            nonlocal end_changes_count
            end_changes_count += 1

        with l2.begin_changes_event.listen(begin_changes), l2.end_changes_event.listen(end_changes):
            l.insert_item(0, "5")
            l.remove_item(0)

        self.assertEqual(2, begin_changes_count)
        self.assertEqual(2, end_changes_count)

    def test_filtered_list_sends_begin_end_changes_for_grouped_insert_and_remove(self):
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l2 = ListModel.FilteredListModel(container=l, items_key="items")
        l2.sort_key = lambda x: x

        begin_changes_count = 0
        end_changes_count = 0

        def begin_changes(key):
            nonlocal begin_changes_count
            begin_changes_count += 1

        def end_changes(key):
            nonlocal end_changes_count
            end_changes_count += 1

        with l2.begin_changes_event.listen(begin_changes), l2.end_changes_event.listen(end_changes):
            with l2.changes():
                l.insert_item(0, "5")
                l.insert_item(0, "6")
                l.remove_item(0)
                l.remove_item(0)

        self.assertEqual(1, begin_changes_count)
        self.assertEqual(1, end_changes_count)

    def test_filtered_list_does_not_access_container_when_closing(self):
        class Container(Observable.Observable):
            def __init__(self):
                super().__init__()
                self.__items = [1, 2, 3]
                self.closed = False

            def close(self):
                self.closed = True

            @property
            def items(self):
                if not self.closed:
                    return self.__items
                return None

        c = Container()
        l2 = ListModel.FilteredListModel(container=c, items_key="items")
        c.close()
        l2.close()

    def test_initial_mapped_model_values_are_correct(self):
        l = ListModel.ListModel("items")
        l.append_item(A("1"))
        l.append_item(A("2"))
        l2 = ListModel.MappedListModel(container=l, master_items_key="items", items_key="itemsb", map_fn=B)
        self.assertEqual([b.s for b in map(B, l.items)], [b.s for b in l2.items])
        self.assertEqual(l2.itemsb, l2.items)
        self.assertEqual("2_B", l2.items[1].s)

    def test_mapped_model_values_after_insert_are_correct(self):
        l = ListModel.ListModel("items")
        l.append_item(A("1"))
        l.append_item(A("2"))
        l2 = ListModel.MappedListModel(container=l, master_items_key="items", items_key="itemsb", map_fn=B)
        l.insert_item(1, A("1.5"))
        self.assertEqual([b.s for b in map(B, l.items)], [b.s for b in l2.items])
        self.assertEqual(l2.itemsb, l2.items)
        self.assertEqual("1.5_B", l2.items[1].s)

    def test_mapped_model_values_after_delete_are_correct(self):
        l = ListModel.ListModel("items")
        l.append_item(A("1"))
        l.append_item(A("2"))
        l.append_item(A("3"))
        l2 = ListModel.MappedListModel(container=l, master_items_key="items", items_key="itemsb", map_fn=B)
        l.remove_item(1)
        self.assertEqual([b.s for b in map(B, l.items)], [b.s for b in l2.items])
        self.assertEqual(l2.itemsb, l2.items)
        self.assertEqual("3_B", l2.items[1].s)

    def test_mapped_model_selection_after_insert_are_correct(self):
        l = ListModel.ListModel("items")
        l.append_item(A("1"))
        l.append_item(A("2"))
        l2 = ListModel.MappedListModel(container=l, master_items_key="items", items_key="itemsb", map_fn=B)
        s = l2.make_selection()
        s.add(0)
        s.add(1)
        l.insert_item(1, A("1.5"))
        self.assertEqual({0, 2}, s.indexes)

    def test_mapped_model_selection_after_delete_are_correct(self):
        l = ListModel.ListModel("items")
        l.append_item(A("1"))
        l.append_item(A("2"))
        l.append_item(A("3"))
        l2 = ListModel.MappedListModel(container=l, master_items_key="items", items_key="itemsb", map_fn=B)
        s = l2.make_selection()
        s.add(0)
        s.add(2)
        l.remove_item(1)
        self.assertEqual({0, 1}, s.indexes)

    def test_mapped_list_sends_begin_end_changes_for_single_insert_and_remove(self):
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l1 = ListModel.FilteredListModel(container=l, master_items_key="items", items_key="mitems")
        l1.sort_key = lambda x: x
        l2 = ListModel.MappedListModel(container=l1, master_items_key="mitems", items_key="items")

        begin_changes_count = 0
        end_changes_count = 0

        def begin_changes(key):
            nonlocal begin_changes_count
            begin_changes_count += 1

        def end_changes(key):
            nonlocal end_changes_count
            end_changes_count += 1

        with l2.begin_changes_event.listen(begin_changes), l2.end_changes_event.listen(end_changes):
            l.insert_item(0, "5")
            l.remove_item(0)

        self.assertEqual(2, begin_changes_count)
        self.assertEqual(2, end_changes_count)

    def test_mapped_list_sends_begin_end_changes_for_grouped_insert_and_remove(self):
        l = ListModel.ListModel("items")
        l.append_item("3")
        l.append_item("1")
        l.append_item("4")
        l.append_item("2")
        l1 = ListModel.FilteredListModel(container=l, master_items_key="items", items_key="mitems")
        l1.sort_key = lambda x: x
        l2 = ListModel.MappedListModel(container=l1, master_items_key="mitems", items_key="items")

        begin_changes_count = 0
        end_changes_count = 0

        def begin_changes(key):
            nonlocal begin_changes_count
            begin_changes_count += 1

        def end_changes(key):
            nonlocal end_changes_count
            end_changes_count += 1

        with l2.begin_changes_event.listen(begin_changes), l2.end_changes_event.listen(end_changes):
            with l2.changes():
                l.insert_item(0, "5")
                l.insert_item(0, "6")
                l.remove_item(0)
                l.remove_item(0)

        self.assertEqual(1, begin_changes_count)
        self.assertEqual(1, end_changes_count)

    def test_flattened_model_initializes_properly(self):
        l = ListModel.ListModel("as")
        bs1 = ListModel.ListModel("bs")
        bs1.append_item("11")
        bs1.append_item("12")
        bs2 = ListModel.ListModel("bs")
        bs3 = ListModel.ListModel("bs")
        bs3.append_item("31")
        bs3.append_item("32")
        bs3.append_item("33")
        l.append_item(bs1)
        l.append_item(bs2)
        l.append_item(bs3)
        f = ListModel.FlattenedListModel(container=l, master_items_key="as", child_items_key="bs", items_key="cs")
        self.assertEqual(["11", "12", "31", "32", "33"], f.cs)

    def test_flattened_model_inserts_master_item_properly(self):
        l = ListModel.ListModel("as")
        bs1 = ListModel.ListModel("bs")
        bs1.append_item("11")
        bs1.append_item("12")
        bs2 = ListModel.ListModel("bs")
        bs3 = ListModel.ListModel("bs")
        bs3.append_item("31")
        bs3.append_item("32")
        bs3.append_item("33")
        l.append_item(bs1)
        l.append_item(bs2)
        l.append_item(bs3)
        f = ListModel.FlattenedListModel(container=l, master_items_key="as", child_items_key="bs", items_key="cs")
        bs4 = ListModel.ListModel("bs")
        bs4.append_item("41")
        bs4.append_item("42")
        l.insert_item(1, bs4)
        self.assertEqual(["11", "12", "41", "42", "31", "32", "33"], f.cs)

    def test_flattened_model_removes_master_item_properly(self):
        l = ListModel.ListModel("as")
        bs1 = ListModel.ListModel("bs")
        bs1.append_item("11")
        bs1.append_item("12")
        bs2 = ListModel.ListModel("bs")
        bs3 = ListModel.ListModel("bs")
        bs3.append_item("31")
        bs3.append_item("32")
        bs3.append_item("33")
        l.append_item(bs1)
        l.append_item(bs2)
        l.append_item(bs3)
        f = ListModel.FlattenedListModel(container=l, master_items_key="as", child_items_key="bs", items_key="cs")
        l.remove_item(0)
        self.assertEqual(["31", "32", "33"], f.cs)

    def test_flattened_model_inserts_child_item_properly(self):
        l = ListModel.ListModel("as")
        bs1 = ListModel.ListModel("bs")
        bs1.append_item("11")
        bs1.append_item("12")
        bs2 = ListModel.ListModel("bs")
        bs3 = ListModel.ListModel("bs")
        bs3.append_item("31")
        bs3.append_item("32")
        bs3.append_item("33")
        l.append_item(bs1)
        l.append_item(bs2)
        l.append_item(bs3)
        f = ListModel.FlattenedListModel(container=l, master_items_key="as", child_items_key="bs", items_key="cs")
        bs1.insert_item(1, "115")
        self.assertEqual(["11", "115", "12", "31", "32", "33"], f.cs)

    def test_flattened_model_removes_child_item_properly(self):
        l = ListModel.ListModel("as")
        bs1 = ListModel.ListModel("bs")
        bs1.append_item("11")
        bs1.append_item("12")
        bs2 = ListModel.ListModel("bs")
        bs3 = ListModel.ListModel("bs")
        bs3.append_item("31")
        bs3.append_item("32")
        bs3.append_item("33")
        l.append_item(bs1)
        l.append_item(bs2)
        l.append_item(bs3)
        f = ListModel.FlattenedListModel(container=l, master_items_key="as", child_items_key="bs", items_key="cs")
        bs1.remove_item(1)
        self.assertEqual(["11", "31", "32", "33"], f.cs)

    def test_flattened_model_with_empty_master_item_closes_properly(self):
        l = ListModel.ListModel("as")
        bs1 = ListModel.ListModel("bs")
        bs1.append_item("11")
        bs2 = ListModel.ListModel("bs")
        bs3 = ListModel.ListModel("bs")
        bs3.append_item("31")
        l.append_item(bs1)
        l.append_item(bs2)
        l.append_item(bs3)
        f = ListModel.FlattenedListModel(container=l, master_items_key="as", child_items_key="bs", items_key="cs")
        with contextlib.closing(f):
            pass


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

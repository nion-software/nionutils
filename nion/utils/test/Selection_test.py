# standard libraries
import logging
import unittest

# local libraries
from nion.utils import Selection


class TestSelection(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_extending_selection_with_no_anchor_behaves_sensibly(self):
        s = Selection.IndexedSelection()
        s.extend(0)
        self.assertEqual({0}, s.indexes)
        self.assertEqual(0, s.anchor_index)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

import unittest

from nion.utils import Color


class TestColorClass(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_hex_color_from_named_color(self) -> None:
        self.assertEqual("#d8bfd8", Color.Color("thistle").hex_color_str)
        self.assertEqual("#123456", Color.Color("#123456").hex_color_str)
        self.assertEqual("#80123456", Color.Color("#80123456").hex_color_str)
        self.assertEqual("#123", Color.Color("#123").hex_color_str)
        self.assertEqual("#8123", Color.Color("#8123").hex_color_str)
        self.assertEqual("#d8bfd8", Color.Color("rgb(216, 191, 216)").to_color_without_alpha().color_str)
        self.assertEqual("#d8bfd8", Color.Color("rgba(216, 191, 216, 0.5)").to_color_without_alpha().color_str)
        self.assertEqual(None, Color.Color(None).hex_color_str)

    def test_color_to_named_color(self) -> None:
        self.assertEqual("thistle", Color.Color("thistle").to_named_color_without_alpha().color_str)
        self.assertEqual("thistle", Color.Color("#d8bfd8").to_named_color_without_alpha().color_str)
        self.assertEqual("thistle", Color.Color("#80d8bfd8").to_named_color_without_alpha().color_str)
        self.assertEqual("thistle", Color.Color("#d8bfd8").to_named_color_without_alpha().color_str)
        self.assertEqual("thistle", Color.Color("rgb(216, 191, 216)").to_named_color_without_alpha().color_str)
        self.assertEqual("thistle", Color.Color("rgba(216, 191, 216, 0.5)").to_named_color_without_alpha().color_str)
        self.assertEqual(None, Color.Color().to_named_color_without_alpha().color_str)

    def test_color_without_alpha(self) -> None:
        self.assertEqual("thistle", Color.Color("thistle").to_color_without_alpha().color_str)
        self.assertEqual("#123456", Color.Color("#123456").to_color_without_alpha().color_str)
        self.assertEqual("#123456", Color.Color("#80123456").to_color_without_alpha().color_str)
        self.assertEqual("#123", Color.Color("#123").to_color_without_alpha().color_str)
        self.assertEqual("#123", Color.Color("#8123").to_color_without_alpha().color_str)
        self.assertEqual("#d8bfd8", Color.Color("rgb(216, 191, 216)").to_color_without_alpha().color_str)
        self.assertEqual("#d8bfd8", Color.Color("rgba(216, 191, 216, 0.5)").to_color_without_alpha().color_str)
        self.assertEqual(None, Color.Color(None).to_color_without_alpha().color_str)

    def test_color_with_alpha(self) -> None:
        self.assertEqual("#40d8bfd8", Color.Color("thistle").to_color_with_alpha(0.25).color_str)
        self.assertEqual("#ffd8bfd8", Color.Color("thistle").to_color_with_alpha(1.00).color_str)
        self.assertEqual("#00d8bfd8", Color.Color("thistle").to_color_with_alpha(0.00).color_str)
        self.assertEqual("#c0d8bfd8", Color.Color("#d8bfd8").to_color_with_alpha(0.75).color_str)
        self.assertEqual("#80204060", Color.Color("#246").to_color_with_alpha(0.50).color_str)
        self.assertEqual("#ff204060", Color.Color("#246").to_color_with_alpha(1.50).color_str)
        self.assertEqual("#00204060", Color.Color("#246").to_color_with_alpha(-1.50).color_str)

    def test_matches_without_alpha(self) -> None:
        self.assertTrue(Color.Color("thistle").matches_without_alpha(Color.Color("#d8bfd8")))
        self.assertTrue(Color.Color("thistle").matches_without_alpha(Color.Color("rgb(216, 191, 216)")))
        self.assertTrue(Color.Color("thistle").matches_without_alpha(Color.Color("rgba(216, 191, 216, 0.5)")))
        self.assertTrue(Color.Color("rgb(216, 191, 216)").matches_without_alpha(Color.Color("rgba(216, 191, 216, 0.5)")))
        self.assertTrue(Color.Color("#123").matches_without_alpha(Color.Color("#102030")))
        self.assertTrue(Color.Color("#123").matches_without_alpha(Color.Color("#80102030")))
        self.assertTrue(Color.Color("#8123").matches_without_alpha(Color.Color("#80102030")))
        self.assertTrue(Color.Color("#8123").matches_without_alpha(Color.Color("#102030")))

    def test_color_equals(self) -> None:
        self.assertEqual(Color.Color("thistle"), Color.Color("#d8bfd8"))
        self.assertNotEqual(Color.Color("rgb(216, 191, 216)"), Color.Color("rgba(216, 191, 216, 0.5)"))

    def test_color_hash(self) -> None:
        d = {Color.Color("thistle"): Color.Color("#d8bfd8")}
        self.assertEqual(d[Color.Color("thistle")], Color.Color("#d8bfd8"))

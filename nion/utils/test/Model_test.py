# standard libraries
import asyncio
import logging
import unittest
import weakref

# third party libraries
# None

# local libraries
from nion.utils import Model
from nion.utils import Stream


class TestModelClass(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_refcounts(self) -> None:
        # property model
        model = Model.PropertyModel[int](0)
        model_ref = weakref.ref(model)
        del model
        self.assertIsNone(model_ref())
        # func stream model (ugh)
        model2 = Model.FuncStreamValueModel(Stream.ValueStream(lambda: None), asyncio.get_event_loop())
        model_ref2 = weakref.ref(model2)
        del model2
        self.assertIsNone(model_ref2())
        # stream value model
        model3 = Model.StreamValueModel(Stream.ValueStream(0))
        model_ref3 = weakref.ref(model3)
        del model3
        self.assertIsNone(model_ref3())


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

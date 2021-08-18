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

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_refcounts(self):
        # property model
        model = Model.PropertyModel(0)
        model_ref = weakref.ref(model)
        del model
        self.assertIsNone(model_ref())
        # func stream model (ugh)
        model = Model.FuncStreamValueModel(Stream.ValueStream(lambda: None), asyncio.get_event_loop())
        model_ref = weakref.ref(model)
        del model
        self.assertIsNone(model_ref())
        # stream value model
        model = Model.StreamValueModel(Stream.ValueStream(0))
        model_ref = weakref.ref(model)
        del model
        self.assertIsNone(model_ref())


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

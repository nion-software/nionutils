# standard libraries
import logging
import unittest
import weakref

# third party libraries
# None

# local libraries
from nion.utils import Model
from nion.utils import Stream


class TestStreamClass(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_refcounts(self):
        # map stream, value stream
        stream = Stream.MapStream(Stream.ValueStream(0), lambda x: x)
        stream_ref = weakref.ref(stream)
        del stream
        self.assertIsNone(stream_ref())
        # combine stream
        stream = Stream.CombineLatestStream([Stream.ValueStream(0), Stream.ValueStream(0)])
        stream_ref = weakref.ref(stream)
        del stream
        self.assertIsNone(stream_ref())
        # debounce
        stream = Stream.DebounceStream(Stream.ValueStream(0), 0.0)
        stream_ref = weakref.ref(stream)
        del stream
        self.assertIsNone(stream_ref())
        # sample
        stream = Stream.SampleStream(Stream.ValueStream(0), 0.0)
        stream_ref = weakref.ref(stream)
        del stream
        self.assertIsNone(stream_ref())
        # property changed event stream
        stream = Stream.PropertyChangedEventStream(Model.PropertyModel(0), "value")
        stream_ref = weakref.ref(stream)
        del stream
        self.assertIsNone(stream_ref())
        # optional stream
        stream = Stream.OptionalStream(Stream.ValueStream(0), lambda x: True)
        stream_ref = weakref.ref(stream)
        del stream
        self.assertIsNone(stream_ref())
        # value stream action
        action = Stream.ValueStreamAction(Stream.ValueStream(0), lambda x: None)
        action_ref = weakref.ref(action)
        del action
        self.assertIsNone(action_ref())
        # value change stream
        stream = Stream.ValueChangeStream(Stream.ValueStream(0))
        stream_ref = weakref.ref(stream)
        del stream
        self.assertIsNone(stream_ref())


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

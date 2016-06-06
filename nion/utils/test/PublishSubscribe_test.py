# standard libraries
import unittest
import uuid

# third party libraries
# None

# local libraries
from nion.utils import PublishSubscribe


class ObjectWithUUID(object):

    def __init__(self):
        self.uuid = uuid.uuid4()


class TestPersistentObjectContextClass(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_subscribing_to_publisher_twice_works(self):
        publisher = PublishSubscribe.Publisher()
        one = list()
        two = list()
        def handle_one(value):
            one.append(value)
        def handle_two(value):
            two.append(value)
        subscription1 = publisher.subscribex(PublishSubscribe.Subscriber(handle_one))
        subscription2 = publisher.subscribex(PublishSubscribe.Subscriber(handle_two))
        publisher.notify_next_value(5)
        self.assertEqual(one, [5, ])
        self.assertEqual(two, [5, ])
        subscription1.close()
        publisher.notify_next_value(6)
        self.assertEqual(one, [5, ])
        self.assertEqual(two, [5, 6])
        subscription2 = None
        publisher.notify_next_value(7)
        self.assertEqual(one, [5, ])
        self.assertEqual(two, [5, 6])

    def test_subscribing_with_select_works(self):
        publisher = PublishSubscribe.Publisher()
        one = list()
        def handle_one(value):
            one.append(value)
        subscription1 = publisher.select(lambda x: x*2).subscribex(PublishSubscribe.Subscriber(handle_one))
        publisher.notify_next_value(5)
        self.assertEqual(one, [10, ])

    def test_subscribing_with_select_twice_works(self):
        publisher = PublishSubscribe.Publisher()
        one = list()
        two = list()
        def handle_one(value):
            one.append(value)
        def handle_two(value):
            two.append(value)
        subscription1 = publisher.select(lambda x: x*2).subscribex(PublishSubscribe.Subscriber(handle_one))
        subscription2 = publisher.select(lambda x: x*3).subscribex(PublishSubscribe.Subscriber(handle_two))
        publisher.notify_next_value(5)
        self.assertEqual(one, [10, ])
        self.assertEqual(two, [15, ])

    def test_subscribing_with_cache_twice_works(self):
        publisher = PublishSubscribe.Publisher()
        one = list()
        two = list()
        def handle_one(value):
            one.append(value)
        def handle_two(value):
            two.append(value)
        subscription1 = publisher.select(lambda x: x*2).cache().subscribex(PublishSubscribe.Subscriber(handle_one))
        subscription2 = publisher.select(lambda x: x*3).cache().subscribex(PublishSubscribe.Subscriber(handle_two))
        publisher.notify_next_value(5)
        self.assertEqual(one, [10, ])
        self.assertEqual(two, [15, ])
        publisher.notify_next_value(5)
        self.assertEqual(one, [10, ])
        self.assertEqual(two, [15, ])
        publisher.notify_next_value(6)
        self.assertEqual(one, [10, 12])
        self.assertEqual(two, [15, 18])

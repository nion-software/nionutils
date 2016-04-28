import logging
import threading
import weakref


class Subscription(object):

    def __init__(self, publisher, subscriber, closer):
        self.__publisher = publisher
        self.subscriber = subscriber
        self.__closer = closer

    def close(self):
        if self.__closer:
            self.__closer(weakref.ref(self))
            self.__publisher = None
            self.subscriber = None
            self.__closer = None


class Publisher(object):

    def __init__(self):
        super(Publisher, self).__init__()
        self.__weak_subscriptions = []
        self.__weak_subscriptions_mutex = threading.RLock()
        self.on_subscribe = None

    def close(self):
        self.on_subscribe = None

    @property
    def _subscriptions(self):
        """Return the subscriptions list. Useful for debugging."""
        with self.__weak_subscriptions_mutex:
            return [weak_subscription() for weak_subscription in self.__weak_subscriptions]

    # Add a listener.
    def subscribex(self, subscriber):
        with self.__weak_subscriptions_mutex:
            assert subscriber is not None
            assert isinstance(subscriber, Subscriber)
            subscription = Subscription(self, subscriber, self.__unsubscribe)
            self.__weak_subscriptions.append(weakref.ref(subscription, self.__unsubscribe))
        if self.on_subscribe:  # outside of lock
            self.on_subscribe(subscriber)
        return subscription

    def __unsubscribe(self, weak_subscription):
        with self.__weak_subscriptions_mutex:
            if weak_subscription in self.__weak_subscriptions:
                self.__weak_subscriptions.remove(weak_subscription)

    # Send a message to the listeners
    def __notify_subscribers(self, fn, subscriber1, *args, **keywords):
        try:
            with self.__weak_subscriptions_mutex:
                subscriptions = [weak_subscription() for weak_subscription in self.__weak_subscriptions]
            for subscription in subscriptions:
                subscriber = subscription.subscriber
                if hasattr(subscriber, fn) and (subscriber1 is None or subscriber == subscriber1):
                    getattr(subscriber, fn)(*args, **keywords)
        except Exception as e:
            import traceback
            logging.debug("Notify Subscription Error: %s", e)
            traceback.print_exc()
            traceback.print_stack()

    def notify_next_value(self, value, subscriber=None):
        self.__notify_subscribers("publisher_next_value", subscriber, value)

    def notify_error(self, exception, subscriber=None):
        self.__notify_subscribers("publisher_error", subscriber, exception)

    def notify_complete(self, subscriber=None):
        self.__notify_subscribers("publisher_complete", subscriber)

    def select(self, select_fn):
        return PublisherSelect(self, select_fn)

    def cache(self):
        return PublisherCache(self)


class PublisherSelect(Publisher):

    def __init__(self, publisher, select_fn):
        super(PublisherSelect, self).__init__()
        self.__select_fn = select_fn
        self.__last_value = None
        def next_value(value):
            self.__last_value = self.__select_fn(value)
            self.notify_next_value(self.__last_value)
        self.__subscription = publisher.subscribex(Subscriber(next_value))

    def close(self):
        self.__subscription.close()
        self.__subscription = None
        self.__select_fn = None
        self.__last_value = None
        super(PublisherSelect, self).close()

    def subscribex(self, subscriber):
        subscription = super(PublisherSelect, self).subscribex(subscriber)
        if self.__last_value:
            self.notify_next_value(self.__last_value)
        return  subscription


class PublisherCache(Publisher):

    def __init__(self, publisher):
        super(PublisherCache, self).__init__()
        self.__cached_value = None
        def next_value(value):
            if value != self.__cached_value:
                self.notify_next_value(value)
                self.__cached_value = value
        self.__subscription = publisher.subscribex(Subscriber(next_value))

    def close(self):
        self.__subscription.close()
        self.__subscription = None
        self.__cached_value = None
        super(PublisherCache, self).close()

    def subscribex(self, subscriber):
        subscription = super(PublisherCache, self).subscribex(subscriber)
        if self.__cached_value:
            self.notify_next_value(self.__cached_value)
        return subscription


class Subscriber(object):

    def __init__(self, next_fn=None, error_fn=None, complete_fn=None):
        self.__next_fn = next_fn
        self.__error_fn = error_fn
        self.__complete_fn = complete_fn

    def publisher_next_value(self, value):
        if self.__next_fn:
            self.__next_fn(value)

    def publisher_error(self, exception):
        if self.__error_fn:
            self.__error_fn(exception)

    def publisher_complete(self):
        if self.__complete_fn:
            self.__complete_fn()

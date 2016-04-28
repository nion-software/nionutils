import logging
import threading
import weakref


class Broadcaster:

    def __init__(self):
        super().__init__()
        self.__weak_listeners = []
        self.__weak_listeners_mutex = threading.RLock()

    # Add a listener.
    def add_listener(self, listener):
        with self.__weak_listeners_mutex:
            assert listener is not None
            def remove_listener(weak_listener):
                with self.__weak_listeners_mutex:
                    self.__weak_listeners.remove(weak_listener)
            self.__weak_listeners.append(weakref.ref(listener, remove_listener))

    # Remove a listener.
    def remove_listener(self, listener):
        with self.__weak_listeners_mutex:
            assert listener is not None
            self.__weak_listeners.remove(weakref.ref(listener))

    # Send a message to the listeners
    def notify_listeners(self, fn, *args, **keywords):
        try:
            with self.__weak_listeners_mutex:
                listeners = [weak_listener() for weak_listener in self.__weak_listeners]
            for listener in listeners:
                if hasattr(listener, fn):
                    getattr(listener, fn)(*args, **keywords)
        except Exception as e:
            import traceback
            logging.debug("Notify Error: %s", e)
            traceback.print_exc()
            traceback.print_stack()

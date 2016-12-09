"""
    Model classes. Useful for bindings.
"""

# standard libraries
import operator

# third party libraries
# none

# local libraries
from . import Observable


class PropertyModel(Observable.Observable):

    """
        Holds a value which can be observed for changes. The value can be any type that supports equality test.

        An optional on_value_changed method gets called when the value changes.
    """

    def __init__(self, value=None, cmp=None):
        super(PropertyModel, self).__init__()
        self.__value = value
        self.__cmp = cmp if cmp else operator.eq
        self.on_value_changed = None

    def close(self):
        self.on_value_changed = None

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if self.__value is None:
            not_equal = value is not None
        elif value is None:
            not_equal = self.__value is not None
        else:
            not_equal = not self.__cmp(value, self.__value)
        if not_equal:
            self.__value = value
            self.notify_property_changed("value")
            if self.on_value_changed:
                self.on_value_changed(value)

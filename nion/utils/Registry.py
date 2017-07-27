"""
An registry for objects by id, uuid, type.
"""

# standard libraries
import typing

# local libraries
from . import Event

# third party libraries
# None


class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class ComponentManager(metaclass=Singleton):
    """The ComponentManager is a Singleton that implements the registry."""
    def __init__(self):
        self.__component_types = dict()
        self.__components_by_type = dict()
        self.component_registered_event = Event.Event()
        self.component_unregistered_event = Event.Event()

    def get_components_by_type(self, component_type:str) -> typing.Set[typing.Any]:
        return self.__components_by_type.get(component_type, list())

    def register(self, component, component_types: typing.Set[str]) -> None:
        assert component not in self.__component_types
        for component_type in component_types:
            component_set = self.__components_by_type.setdefault(component_type, set())
            component_set.add(component)
        self.__component_types[component] = component_types
        self.component_registered_event.fire(component, component_types)

    def unregister(self, component) -> None:
        assert component in self.__component_types
        for component_type in self.__component_types[component]:
            self.__components_by_type.get(component_type).remove(component)
        component_types = self.__component_types.pop(component)
        self.component_unregistered_event.fire(component, component_types)


def get_components_by_type(component_type: str) -> typing.Set[typing.Any]:
    """Returns set of components matching component_type."""
    return ComponentManager().get_components_by_type(component_type)


def register_component(component, component_types: typing.Set[str]) -> None:
    """Register a component and associated it with the set of types. This will trigger a component_registered_event."""
    ComponentManager().register(component, component_types)


def unregister_component(component) -> None:
    """Unregister a component. This will trigger a component_unregistered_event. The component must have been previously registered."""
    ComponentManager().unregister(component)


def listen_component_registered_event(listener_fn) -> Event.EventListener:
    """Add a listener for the component registered event."""
    return ComponentManager().component_registered_event.listen(listener_fn)


def listen_component_unregistered_event(listener_fn) -> Event.EventListener:
    """Add a listener for the component unregistered event."""
    return ComponentManager().component_unregistered_event.listen(listener_fn)

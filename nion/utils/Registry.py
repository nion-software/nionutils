"""
An registry for objects by id, uuid, type.
"""

# standard libraries
import abc
import typing
import uuid

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


class Component(abc.ABC):
    """Components must implement these read-only properties."""

    @property
    @abc.abstractmethod
    def component_types(self) -> typing.Set[str]:
        """The list of component types."""
        ...

    @property
    @abc.abstractmethod
    def component_id(self) -> str:
        """The component id, must be a unique identifier starting with letter comprised of letter, numbers, underscores."""
        ...

    @property
    @abc.abstractmethod
    def component_uuid(self) -> uuid.UUID:
        """The component uuid, must be unique."""
        ...


class ComponentManager(metaclass=Singleton):
    """The ComponentManager is a Singleton that implements the registry."""
    def __init__(self):
        self.__component_by_id = dict()
        self.__components_by_type = dict()
        self.__component_by_uuid = dict()
        self.component_registered_event = Event.Event()
        self.component_unregistered_event = Event.Event()

    def get_component(self, *, component_type: str=None, component_id: str=None, component_uuid: uuid.UUID=None, default=None) -> Component:
        if component_id:
            return self.__component_by_id.get(component_id, default)
        if component_type:
            components = self.__components_by_type.get(component_type)
            if components and len(components) == 1:
                return components[0]
        if component_uuid:
            return self.__component_by_uuid.get(component_uuid, default)
        return default

    def get_components_by_type(self, component_type:str) -> typing.Set[Component]:
        return self.__components_by_type.get(component_type, list())

    def register(self, component: Component) -> None:
        self.__component_by_id[component.component_id] = component
        self.__component_by_uuid[component.component_uuid] = component
        for component_type in component.component_types:
            component_set = self.__components_by_type.setdefault(component_type, set())
            component_set.add(component)
        self.component_registered_event.fire(component)

    def unregister(self, component: Component) -> None:
        del self.__component_by_id[component.component_id]
        del self.__component_by_uuid[component.component_uuid]
        for component_type in component.component_types:
            self.__components_by_type.get(component_type).remove(component)
        self.component_unregistered_event.fire(component)


def get_component(*, component_type: str=None, component_id: str=None, component_uuid: uuid.UUID=None, default=None) -> Component:
    """Returns component matching component_type, component_id, component_uuid or a default value if none is found.
    
    A component matching component_type will only be returned if it is unique. Otherwise use get_components_by_type.
    """
    return ComponentManager().get_component(component_type=component_type, component_id=component_id, component_uuid=component_uuid, default=default)

def get_components_by_type(type: str) -> typing.Set[Component]:
    """Returns set of components matching component_type."""
    return ComponentManager().get_components_by_type(type)

def register_component(component: Component) -> None:
    """Register a component. This will trigger a component_registered_event. The component id and uuid must be unique."""
    ComponentManager().register(component)

def unregister_component(component: Component) -> None:
    """Unregister a component. This will trigger a component_unregistered_event. The component must have been previously registered."""
    ComponentManager().unregister(component)

def listen_component_registered_event(listener_fn) -> Event.EventListener:
    """Add a listener for the component registered event."""
    return ComponentManager().component_registered_event.listen(listener_fn)

def listen_component_unregistered_event(listener_fn) -> Event.EventListener:
    """Add a listener for the component unregistered event."""
    return ComponentManager().component_unregistered_event.listen(listener_fn)

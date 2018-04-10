"""List and filtered list model."""

# standard libraries
import copy
import functools
import operator
import re
import threading
import typing

# third party libraries
# None

# local libraries
from nion.utils import Observable
from nion.utils import Model
from nion.utils import ListModel as ListModelModule


# TODO: logical types: datetime, timestamp, uuid, etc.


MDescription = typing.Dict  # when napolean works: typing.NewType("MDescription", typing.Dict)
MFields = typing.List  # when napolean works: typing.NewType("MFields", typing.List)


def create_string() -> MDescription:
    return "string"


def create_boolean() -> MDescription:
    return "boolean"


def create_int() -> MDescription:
    return "int"


def create_float() -> MDescription:
    return "double"


def create_field(name: str=None, type: str=None, *, default=None) -> MDescription:
    d = {"name": name, "type": type}
    if default is not None:
        d["default"] = default
    return d


def create_record(name: str, fields: MFields) -> MDescription:
    return {"type": "record", "name": name, "fields": fields}


def create_array(name: str, items: MDescription) -> MDescription:
    return {"type": "array", "name": name, "items": items}


def construct_model(schema: MDescription, *, field_default=None):
    if schema in ("string", "boolean", "int", "float"):
        return Model.PropertyModel(field_default)
    type = schema.get("type")
    if type in ("string", "boolean", "int", "float"):
        return Model.PropertyModel(field_default)
    elif type == "record":
        return RecordModel(schema)
    elif type == "array":
        return ArrayModel(schema)


class RecordModel(Observable.Observable):

    def __init__(self, schema: MDescription, **kwargs):
        super().__init__()
        self.schema = schema
        self.__field_models = dict()
        for field_schema in schema["fields"]:
            field_name = field_schema["name"]
            field_type = field_schema["type"]
            field_default = field_schema.get("default")
            field_model = construct_model(field_type, field_default=field_default)
            if field_name in kwargs:
                field_model.value = kwargs[field_name]
            self.__field_models[field_name] = field_model

    def __getattr__(self, item):
        if item in self.__field_models:
            return self.__field_models[item]
        raise AttributeError(f"Missing {item}")


class ArrayModel(ListModelModule.ListModel):

    def __init__(self, schema: MDescription):
        super().__init__()
        self.schema = schema

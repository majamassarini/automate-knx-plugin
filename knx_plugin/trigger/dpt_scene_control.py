import copy
from typing import Any


import home
import knx_stack

from knx_plugin.trigger import Equal as Parent


class Activate(Parent):

    DPT = {
        "type": "knx",
        "name": "DPT_SceneControl",
        "addresses": [],
        "fields": {"number": 0, "command": "activate"},
    }

    DEFAULT_EVENTS: list[Any] = []

    def __init__(
        self,
        description: dict,
        events: list[home.Event] = None,
        number: int = None,
    ):
        description["fields"]["number"] = number if number else 0
        super(Activate, self).__init__(description, events)

    @classmethod
    def make(
        cls,
        addresses: list[knx_stack.Address],
        events: list[home.Event] = None,
        number: int = None,
    ):
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description, events, number)
        dsc.addresses = addresses
        return dsc

    @classmethod
    def make_from_yaml(
        cls,
        addresses: list[int],
        events: list[home.Event] = None,
        number: int = None,
    ):
        description: dict[str, Any] = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(description, events, number)

import copy

from typing import List

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

    DEFAULT_EVENTS = []

    def __init__(
        self, description: dict, events: List[home.Event] = None, number: int = None
    ):
        description["fields"]["number"] = number if number else 0
        super(Activate, self).__init__(description, events)

    @classmethod
    def make(
        cls,
        addresses: List[knx_stack.Address],
        events: List[home.Event] = None,
        number: int = None,
    ):
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description, events, number)
        dsc.addresses = addresses
        return dsc

    @classmethod
    def make_from_yaml(
        cls, addresses: List[int], events: List[home.Event] = None, number: int = None
    ):
        description = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(description, events, number)

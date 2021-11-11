import copy

from typing import List

import home
import knx_stack
from knx_plugin.trigger import Equal as Parent


class Equal(Parent):

    DPT = {
        "type": "knx",
        "name": "DPTVimarScene",
        "addresses": [],
        "fields": {"index": 0, "command": "attiva"},
    }

    DEFAULT_EVENTS = [home.event.scene.Event.Triggered]

    def __init__(
        self, description: dict, events: List[home.Event] = None, index: int = None
    ):
        description["fields"]["index"] = index if index else 0
        super(Equal, self).__init__(description, events)

    @classmethod
    def make(
        cls,
        addresses: List[knx_stack.Address],
        events: List[home.Event] = None,
        index: int = None,
    ):
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description, events, index)
        dsc.addresses = addresses
        return dsc

    @classmethod
    def make_from_yaml(
        cls, addresses: List[int], events: List[home.Event] = None, index: int = None
    ):
        description = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(description, events, index)


class EqualNoDefaultEvents(Equal):

    DEFAULT_EVENTS = []

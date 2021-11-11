from typing import List

import home

from knx_plugin.message import Description
from knx_plugin.trigger import Always as Parent, GreaterThan
from knx_plugin.trigger.mean import LesserThan


class Always(Parent):

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Wsp",
        "addresses": [],
        "fields": {"decoded_value": 0},
    }


class Strong(GreaterThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> strong = knx_plugin.trigger.dpt_value_wsp.Strong.make_from_yaml(addresses=[1234], value=8)

    >>> address_table = knx_stack.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> strong.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Wsp",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 8.1}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> strong.is_triggered(another_description)
    True

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Wsp",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 7.9}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> strong.is_triggered(another_description)
    False
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Wsp",
        "addresses": [],
        "fields": {"decoded_value": 4.0},
    }

    DEFAULT_EVENTS = [home.event.wind.Event.Strong]


class Weak(LesserThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> weak = knx_plugin.trigger.dpt_value_wsp.Weak.make_from_yaml(addresses=[1234])

    >>> address_table = knx_stack.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> weak.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Wsp",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 1.2}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> weak.is_triggered(another_description)
    True

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Wsp",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 2.1}}
    ... '''
    >>> fd = io.StringIO(bus_event)
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> weak.is_triggered(another_description)
    True
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Wsp",
        "addresses": [],
        "fields": {"decoded_value": 2.0},
    }

    DEFAULT_EVENTS = [home.event.wind.Event.Weak]
    NUM_OF_SAMPLES = 30

    def __init__(
        self,
        description: Description,
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
    ):
        super(Weak, self).__init__(
            description, events, samples if samples else self.NUM_OF_SAMPLES, value
        )

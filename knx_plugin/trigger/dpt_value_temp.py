from typing import List

import home

from knx_plugin.message import Description
from knx_plugin.trigger import Always as Parent, GreaterThan, InBetween, LesserThan
from knx_plugin.trigger.custom_clima import Report


class Hot(GreaterThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> hot = knx_plugin.trigger.dpt_value_temp.Hot.make_from_yaml(addresses=[1234], value=35)

    >>> address_table = knx_stack.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> hot.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Temp",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 36}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> hot.is_triggered(another_description)
    True
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Temp",
        "addresses": [],
        "fields": {"decoded_value": 25.0},
    }

    DEFAULT_EVENTS = [home.event.temperature.Event.Hot]


class Warm(InBetween):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> warm = knx_plugin.trigger.dpt_value_temp.Warm.make_from_yaml(addresses=[1234])

    >>> address_table = knx_stack.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> warm.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Temp",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 15.5}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> warm.is_triggered(another_description)
    True
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Temp",
        "addresses": [],
        "fields": {"decoded_value": 5.0},
    }

    DEFAULT_EVENTS = [home.event.temperature.Event.Warm]
    RANGE = 20.0

    def __init__(
        self,
        description: Description,
        events: List[home.Event] = None,
        value: float = None,
        range: int = None,
    ):
        super(Warm, self).__init__(
            description, events, value, range if range else self.RANGE
        )


class Cold(LesserThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> cold = knx_plugin.trigger.dpt_value_temp.Cold.make_from_yaml(addresses=[1234])

    >>> address_table = knx_stack.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> cold.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Temp",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 2.5}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> cold.is_triggered(another_description)
    True
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Temp",
        "addresses": [],
        "fields": {"decoded_value": 5.0},
    }

    DEFAULT_EVENTS = [home.event.temperature.Event.Cold]


class Always(Parent):

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Temp",
        "addresses": [],
        "fields": {"decoded_value": 0},
    }


class CustomThermostatReport(Report):
    def make_new_state_from(
        self, another_description: Description, old_state: home.appliance.State
    ):
        new_state = super(CustomThermostatReport, self).make_new_state_from(
            another_description, old_state
        )
        new_state = new_state.next(self._decode_temperatura(another_description))
        return new_state

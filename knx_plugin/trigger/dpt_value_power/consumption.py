from typing import List

import home
from knx_plugin.trigger import mean, GreaterThan, LesserThan


class No(LesserThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> addresses = [knx_stack.GroupAddress(free_style=1234),]
    >>> consuming = knx_plugin.trigger.dpt_value_power.consumption.No.make(addresses=addresses)

    >>> address_table = knx_stack.layer.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.layer.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> consuming.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Power",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": -600}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> consuming.is_triggered(another_description)
    True
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Power",
        "addresses": [],
        "fields": {"decoded_value": 0},
    }

    DEFAULT_EVENTS = [home.event.power.consumption.Event.No]


class Low(mean.InBetween):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> addresses = [knx_stack.GroupAddress(free_style=1234),]
    >>> low = knx_plugin.trigger.dpt_value_power.consumption.Low.make(addresses=addresses)

    >>> address_table = knx_stack.layer.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.layer.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> low.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Power",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 2}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> low.is_triggered(another_description)
    True

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Power",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 4000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> low.is_triggered(another_description)
    False
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Power",
        "addresses": [],
        "fields": {"decoded_value": 1},
    }

    DEFAULT_EVENTS = [home.event.power.consumption.Event.Low]
    NUM_OF_SAMPLES = 1
    RANGE = 3300  # W

    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        range: int = None,
        value: float = None,
    ):
        super(Low, self).__init__(
            description,
            events,
            samples if samples else self.NUM_OF_SAMPLES,
            value,
            range if range else self.RANGE,
        )


class High(mean.InBetween):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> addresses = [knx_stack.GroupAddress(free_style=1234),]
    >>> low = knx_plugin.trigger.dpt_value_power.consumption.High.make(addresses=addresses)

    >>> address_table = knx_stack.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> low.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Power",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 7001}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> low.is_triggered(another_description)
    True

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Power",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 8000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> low.is_triggered(another_description)
    False
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Power",
        "addresses": [],
        "fields": {"decoded_value": 7000},
    }

    DEFAULT_EVENTS = [home.event.power.consumption.Event.High]
    NUM_OF_SAMPLES = 1
    RANGE = 699  # W

    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        range: int = None,
        value: float = None,
    ):
        super(High, self).__init__(
            description,
            events,
            samples if samples else self.NUM_OF_SAMPLES,
            value,
            range if range else self.RANGE,
        )


class Overhead(GreaterThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> addresses = [knx_stack.GroupAddress(free_style=1234),]
    >>> consuming = knx_plugin.trigger.dpt_value_power.consumption.Overhead.make(addresses=addresses)

    >>> address_table = knx_stack.layer.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.layer.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> consuming.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Power",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 8100}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> consuming.is_triggered(another_description)
    True
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Power",
        "addresses": [],
        "fields": {"decoded_value": 8000},
    }

    DEFAULT_EVENTS = [home.event.power.consumption.Event.High]

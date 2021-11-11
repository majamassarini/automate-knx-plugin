from typing import List

import home

from knx_plugin.trigger import Always as Parent
from knx_plugin.trigger import mean


class Always(Parent):

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Lux",
        "addresses": [],
        "fields": {"decoded_value": 0},
    }


class Brightness(Always):
    """
    Update a State, which holds a brightness attribute,
    with the new measured lux value
    """

    def make_new_state_from(
        self,
        another_description: "knx_plugin.message.Description",
        old_state: home.appliance.State,
    ) -> home.appliance.State:
        new_state = super(Always, self).make_new_state_from(
            another_description, old_state
        )
        new_state.brightness = another_description.dpt.decode()
        return new_state


class Bright(mean.GreaterThan):

    DEFAULT_EVENTS = [home.event.sun.brightness.Event.Bright]
    NUM_OF_SAMPLES = 50

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Lux",
        "addresses": [],
        "fields": {"decoded_value": 45000},
    }

    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
    ):
        super(Bright, self).__init__(
            description, events, samples if samples else self.NUM_OF_SAMPLES, value
        )


class DeepDark(mean.LesserThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> deepdark = knx_plugin.trigger.dpt_value_lux.DeepDark.make_from_yaml(addresses=[1234])

    >>> address_table = knx_stack.layer.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.layer.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> deepdark.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Lux",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 4001}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> deepdark.is_triggered(another_description)
    False

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Lux",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 1000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> deepdark.is_triggered(another_description)
    True
    """

    DEFAULT_EVENTS = [home.event.sun.brightness.Event.DeepDark]
    NUM_OF_SAMPLES = 50

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Lux",
        "addresses": [],
        "fields": {"decoded_value": 4000},
    }

    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
    ):
        super(DeepDark, self).__init__(
            description, events, samples if samples else self.NUM_OF_SAMPLES, value
        )


class Dark(mean.InBetween):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> dark = knx_plugin.trigger.dpt_value_lux.Dark.make_from_yaml(addresses=[1234])

    >>> address_table = knx_stack.layer.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.layer.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> dark.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Lux",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 9000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> dark.is_triggered(another_description)
    True

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Lux",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 60000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> dark.is_triggered(another_description)
    False
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Lux",
        "addresses": [],
        "fields": {"decoded_value": 4000},
    }

    DEFAULT_EVENTS = [home.event.sun.brightness.Event.Dark]
    NUM_OF_SAMPLES = 50
    RANGE = 15000  # lux

    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
        range: int = None,
    ):
        super(Dark, self).__init__(
            description,
            events,
            samples if samples else self.NUM_OF_SAMPLES,
            value,
            range if range else self.RANGE,
        )


from knx_plugin.trigger.dpt_value_lux import balance

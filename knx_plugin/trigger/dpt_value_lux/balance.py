import copy

from typing import List

import home
import knx_stack

from knx_plugin.message import Description
from knx_plugin.trigger import mean


class SunBrightness(mean.Mean):
    """
    It triggers **sun brightness**.
    The sun brightness **mean** is used to calculate a new light Appliance brightness value.
    A *home.appliance.light.event.brightness.Event* has a value in between **[0;100]**.

    If outside sun brightness is high then the new brightness light event value is low
    and the other way around.

    The lowest light brightness event value is given by user in *lowest light brightness*.
    The highest light brightness event value is given by user in *highest light brightness*.
    The *highest light brightness* event is notified when outside *sun brightness value* is lower than *min sun brightness* given by user.
    The *lowest light brightness* event is notified when outside *sun brightness value* is higher than *max sun brightness* given by user.

    In between min and max sun brightness values the system will scale the light brightness.

    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> balance = knx_plugin.trigger.dpt_value_lux.balance.SunBrightness.make_from_yaml([1234], [], 1, 0, 30, 100, 5000, 30000)

    >>> address_table = knx_stack.layer.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.layer.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> balance.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Lux",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 9000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> balance.is_triggered(another_description)
    True
    >>> balance.events[0]
    Balanced brightness: 89%

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Lux",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 5000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> balance.is_triggered(another_description)
    True
    >>> balance.events[0]
    Balanced brightness: 100%

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Lux",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 30000}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> balance.is_triggered(another_description)
    True
    >>> balance.events[0]
    Balanced brightness: 30%
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Lux",
        "addresses": [],
        "fields": {"decoded_value": 0},
    }
    NUM_OF_SAMPLES = 30

    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
        lowest_light_brightness: int = None,
        highest_light_brightness: int = None,
        min_sun_brightness: int = None,
        max_sun_brightness: int = None,
    ):
        super(SunBrightness, self).__init__(
            description, events, samples if samples else self.NUM_OF_SAMPLES, value
        )
        self._lowest_light_brightness = (
            lowest_light_brightness if lowest_light_brightness else 30
        )
        self._highest_light_brightness = (
            highest_light_brightness if highest_light_brightness else 100
        )
        self._min_sun_brightness = min_sun_brightness if min_sun_brightness else 5000
        self._max_sun_brightness = max_sun_brightness if max_sun_brightness else 30000
        self._event = home.appliance.light.event.lux_balancing.brightness.Event(
            self._highest_light_brightness
        )
        self._coefficient = (
            self._highest_light_brightness - self._lowest_light_brightness
        ) / (self._max_sun_brightness - self._min_sun_brightness)

    @classmethod
    def make(
        cls,
        addresses: List[knx_stack.Address],
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
        lowest_light_brightness: int = None,
        highest_light_brightness: int = None,
        min_sun_brightness: int = None,
        max_sun_brightness: int = None,
    ):
        description = copy.deepcopy(cls.DPT)
        dsc = cls(
            description,
            events,
            samples,
            value,
            lowest_light_brightness,
            highest_light_brightness,
            min_sun_brightness,
            max_sun_brightness,
        )
        dsc.addresses = addresses
        return dsc

    @classmethod
    def make_from_yaml(
        cls,
        addresses: List[int],
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
        lowest_light_brightness: int = None,
        highest_light_brightness: int = None,
        min_sun_brightness: int = None,
        max_sun_brightness: int = None,
    ):
        description = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(
            description,
            events,
            samples,
            value,
            lowest_light_brightness,
            highest_light_brightness,
            min_sun_brightness,
            max_sun_brightness,
        )

    def create_brightness_event(
        self,
    ) -> home.appliance.light.event.lux_balancing.brightness.Event:
        if self._mean < self._min_sun_brightness:
            value = self._highest_light_brightness
        elif self._mean > self._max_sun_brightness:
            value = self._lowest_light_brightness
        else:
            value = self._highest_light_brightness - (
                (self._mean - self._min_sun_brightness) * self._coefficient
            )
        return home.appliance.light.event.lux_balancing.brightness.Event(round(value))

    def is_triggered(self, another_description: Description) -> bool:
        if super(SunBrightness, self).is_triggered(another_description):
            self._event = self.create_brightness_event()
            return True
        return False

    @property
    def events(self) -> List[home.Event]:
        a_list = self._events.copy()
        a_list.append(self._event)
        return a_list

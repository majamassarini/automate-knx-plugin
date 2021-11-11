from typing import Union, Type

import home
from knx_plugin.message import Command


class Brightness(Command):
    """
    >>> import home
    >>> import knx_plugin
    >>> command = knx_plugin.command.dpt_brightness.Brightness.make([])
    >>> command._asaps = [1]
    >>> old_state = home.appliance.light.indoor.dimmerable.state.off.State()
    >>> new_state = old_state.next(home.appliance.light.event.brightness.Event(10))
    >>> new_state = new_state.next(home.appliance.light.event.circadian_rhythm.brightness.Event(20))
    >>> new_state = new_state.next(home.appliance.light.event.lux_balancing.brightness.Event(30))
    >>> new_state = new_state.next(home.appliance.light.indoor.dimmerable.event.forced.Event.CircadianRhythm)
    >>> msgs = command.make_msgs_from(old_state, new_state)
    >>> msgs[0].dpt.value
    20
    >>> old_state = new_state.next(home.appliance.light.indoor.dimmerable.event.forced.Event.Not)
    >>> new_state = old_state.next(home.appliance.light.indoor.dimmerable.event.forced.Event.LuxBalance)
    >>> msgs = command.make_msgs_from(old_state, new_state)
    >>> msgs[0].dpt.value
    30
    >>> old_state = new_state.next(home.appliance.light.indoor.dimmerable.event.forced.Event.Not)
    >>> new_state = old_state.next(home.appliance.light.indoor.dimmerable.event.forced.Event.On)
    >>> msgs = command.make_msgs_from(old_state, new_state)
    >>> msgs[0].dpt.value
    10
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Brightness",
        "addresses": [],
        "fields": {"value": 100},
    }

    def make_msgs_from(
        self,
        old_state: Union[
            Type[home.appliance.light.indoor.dimmerable.state.State],
            Type[home.appliance.light.indoor.hue.state.State],
        ],
        new_state: Union[
            Type[home.appliance.light.indoor.dimmerable.state.State],
            Type[home.appliance.light.indoor.hue.state.State],
        ],
    ):
        result = []
        if ((old_state.is_on != new_state.is_on) and new_state.is_on) or (
            (old_state.brightness != new_state.brightness) and new_state.is_on
        ):
            self._dpt.value = new_state.brightness
            result = self.execute()
        return result

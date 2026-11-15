import copy

import knx_stack
import home

from knx_plugin.message import Description
from knx_plugin.trigger import Trigger


class Step(Trigger):

    DPT = {
        "type": "knx",
        "name": "DPT_Control_Dimming",
        "addresses": [],
        "fields": {"step": 0, "direction": "down"},
    }

    def is_triggered(self, another_description: Description) -> bool:
        if super(Step, self).is_triggered(another_description):
            if set(self.asaps).intersection(set(another_description.asaps)):
                triggered = another_description.dpt.step > 0
                self._logger.info(
                    "{} ({} triggered={}):"
                    " dpt.step={}"
                    " dpt.direction={}"
                    " for asaps={}".format(
                        self._dpt_class.__name__,
                        self.__class__.__name__,
                        triggered,
                        self.dpt.step,
                        self.dpt.direction,
                        self.asaps,
                    )
                )
                return triggered
        return False


class BrightnessStep(Step):
    """
    >>> import json
    >>> import home
    >>> import knx_plugin
    >>> trigger = knx_plugin.trigger.dpt_control_dimming.BrightnessStep.make([1234])
    >>> bus_event = '''
    ...     {"name": "DPT_Control_Dimming",
    ...      "addresses": [1234],
    ...      "fields": {"direction": "down", "step": 7}}
    ... '''
    >>> description = (knx_plugin.Description(json.loads(bus_event)))
    >>> old_state = home.appliance.light.indoor.dimmerable.state.on.State()
    >>> new_state = trigger.make_new_state_from(description, old_state)
    >>> new_state.brightness
    10
    """

    DEFAULT_EVENTS = [
        home.appliance.light.indoor.dimmerable.event.forced.Event.On
    ]

    def make_new_state_from(
        self, another_description: Description, old_state: home.appliance.State
    ) -> home.appliance.State:
        step_ = (
            another_description.dpt.step
            if another_description.dpt.direction
            == knx_stack.datapointtypes.DPT_Control_Dimming.Direction.up
            else -another_description.dpt.step
        )

        new_state = super(BrightnessStep, self).make_new_state_from(
            another_description, old_state
        )
        if new_state.brightness + (step_ * 20) > 100:
            new_brightness = 100
        elif new_state.brightness + (step_ * 20) < 10:
            new_brightness = 10
        else:
            new_brightness = new_state.brightness + (step_ * 20)
        new_state.brightness = new_brightness

        return new_state


class VolumeStep(Step):
    """
    A dimming step changes the volume of an appliance that is on by
    ``VOLUME_DELTA`` (up or down), within 0 and 100. The new volume is set
    on the volume property of the current state, so the appliance commands
    send it. An appliance that is off is left as it is.

    >>> import json
    >>> import home
    >>> import knx_plugin
    >>> trigger = knx_plugin.trigger.dpt_control_dimming.VolumeStep.make([1234])
    >>> def step(direction):
    ...     return knx_plugin.Description(json.loads(
    ...         '{"name": "DPT_Control_Dimming", "addresses": [1234],'
    ...         ' "fields": {"direction": "%s", "step": 1}}' % direction))
    >>> player = home.appliance.sound.player
    >>> off = player.state.off.State()
    >>> for event in off.DEFAULTS:
    ...     off = off.next(event)
    >>> on = off.next(player.event.forced.Event.On)
    >>> on = on.next(home.event.sleepiness.Event.Awake)
    >>> on = on.next(player.event.volume.Event(20))
    >>> on.compute(), on.volume
    ('Forced On', 20)
    >>> trigger.make_new_state_from(step("up"), on).volume
    25
    >>> trigger.make_new_state_from(step("down"), on).volume
    15
    >>> trigger.make_new_state_from(step("up"), off) is off
    True
    >>> loud = on.next(home.appliance.sound.player.event.volume.Event(98))
    >>> trigger.make_new_state_from(step("up"), loud).volume
    100
    """

    VOLUME_DELTA = 5

    def make_new_state_from(
        self, another_description: Description, old_state: home.appliance.State
    ) -> home.appliance.State:
        new_state = super(VolumeStep, self).make_new_state_from(
            another_description, old_state
        )
        if not new_state.is_on:
            return old_state
        if new_state is old_state:
            new_state = copy.deepcopy(old_state)
        delta = (
            self.VOLUME_DELTA
            if another_description.dpt.direction
            == knx_stack.datapointtypes.DPT_Control_Dimming.Direction.up
            else -self.VOLUME_DELTA
        )
        new_state.volume = min(100, max(0, new_state.volume + delta))
        return new_state


from knx_plugin.trigger.dpt_control_dimming import step

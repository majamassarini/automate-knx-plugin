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

    DEFAULT_EVENTS = [home.appliance.light.indoor.dimmerable.event.forced.Event.On]

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


from knx_plugin.trigger.dpt_control_dimming import step

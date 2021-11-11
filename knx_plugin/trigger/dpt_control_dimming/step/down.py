from knx_plugin.message import Description
from knx_plugin.trigger import Trigger as Parent


class Trigger(Parent):

    DPT = {
        "type": "knx",
        "name": "DPT_Control_Dimming",
        "addresses": [],
        "fields": {"direction": "down"},
    }

    def is_triggered(self, another_description: Description) -> bool:
        triggered = False
        if super(Trigger, self).is_triggered(another_description):
            triggered = another_description.dpt.direction == self.dpt.direction
        return triggered

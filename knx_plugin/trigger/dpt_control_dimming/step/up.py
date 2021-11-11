from knx_plugin.trigger.dpt_control_dimming.step.down import Trigger as Parent


class Trigger(Parent):

    DPT = {
        "type": "knx",
        "name": "DPT_Control_Dimming",
        "addresses": [],
        "fields": {"direction": "up"},
    }

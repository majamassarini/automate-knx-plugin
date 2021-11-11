import home
from knx_plugin.message import Description
from knx_plugin.trigger import Trigger


class Always(Trigger, home.protocol.Trigger):
    """
    Update a State, which holds a brightness attribute,
    with the new measured brightness value
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Brightness",
        "addresses": [],
        "fields": {"value": 100},
    }

    def make_new_state_from(
        self, another_description: Description, old_state: home.appliance.State
    ) -> home.appliance.State:
        new_state = super(Always, self).make_new_state_from(
            another_description, old_state
        )
        new_state.brightness = another_description.dpt.value
        return new_state

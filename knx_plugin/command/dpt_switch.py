from knx_plugin.command import OnOffAppliance
from knx_plugin.message import Command


class OnOff(Command):
    """
    >>> import home
    >>> import knx_plugin
    >>> old_state = home.appliance.light.indoor.hue.state.off.State()
    >>> new_state = old_state.next(home.appliance.light.indoor.dimmerable.event.forced.Event.On)
    >>> command = knx_plugin.command.dpt_switch.OnOff.make([0xAAAA])
    >>> command._asaps = [1]
    >>> command.make_msgs_from(old_state, new_state)
    [GroupValueWriteReq (DPT_Switch {'action': 'on'} for asap 1)]
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Switch",
        "addresses": [],
        "fields": {"action": "off"},
    }

    def make_msgs_from(
        self,
        old_state: OnOffAppliance,
        new_state: OnOffAppliance,
    ):
        """
        - If Appliance has been turned **on** then send a *dpt_switch on* message on bus
        - If Appliance has been turned **off** then send a *dpt_switch off* message on bus
        """
        result = []
        if old_state.is_on != new_state.is_on:
            if new_state.is_on:
                self._dpt.action = "on"
            else:
                self._dpt.action = "off"
            result = self.execute()
        return result


class OffOn(Command):

    DPT = {
        "type": "knx",
        "name": "DPT_Switch",
        "addresses": [],
        "fields": {"action": "off"},
    }

    def make_msgs_from(
        self,
        old_state: OnOffAppliance,
        new_state: OnOffAppliance,
    ):
        """
        - If Appliance has been turned **on** then send a *dpt_switch off* message on bus
        - If Appliance has been turned **off** then send a *dpt_switch on* message on bus
        """
        result = []
        if old_state.is_on != new_state.is_on:
            if new_state.is_on:
                self._dpt.action = "off"
            else:
                self._dpt.action = "on"
            result = self.execute()
        return result

from knx_plugin.command import OpenCloseAppliance
from knx_plugin.message import Command


class UpDown(Command):

    DPT = {"name": "DPT_UpDown", "addresses": [], "fields": {"direction": "up"}}

    def make_msgs_from(
        self,
        old_state: OpenCloseAppliance,
        new_state: OpenCloseAppliance,
    ):
        """
        - If Appliance has been **closed** then send a *dpt_updown down* message on bus
        - If Appliance has been **opened** then send a *dpt_updown up* message on bus
        """
        result = []
        if old_state.is_opened != new_state.is_opened:
            if new_state.is_opened:
                self._dpt.direction = "up"
            else:
                self._dpt.direction = "down"
            result = self.execute()
        return result


class Up(Command):

    DPT = {"name": "DPT_UpDown", "addresses": [], "fields": {"direction": "up"}}

    def make_msgs_from(
        self, old_state: OpenCloseAppliance, new_state: OpenCloseAppliance
    ):
        """
        - If Appliance has been **closed** do nothing!
        - If Appliance has been **opened** then send a *dpt_updown up* message on bus
        """
        result = []
        if old_state.is_opened != new_state.is_opened:
            if new_state.is_opened:
                self._dpt.direction = "up"
                result = self.execute()
        return result


class Stop(Command):

    DPT = {"name": "DPT_Start", "addresses": [], "fields": {"direction": "stop"}}

    def make_msgs_from(
        self, old_state: OpenCloseAppliance, new_state: OpenCloseAppliance
    ):
        result = []
        if (
            old_state.is_opened == new_state.is_opened
            and old_state.is_closing != new_state.is_closing
        ):
            if new_state.is_closing:
                result = self.execute()
        return result

import home
import copy
import knx_stack

from typing import List
from knx_plugin.message import Description


class Trigger(home.protocol.Trigger, Description):
    """A generic KNX trigger triggered when it has some ASAPs in common with the compared Description"""

    @classmethod
    def make(
        cls, addresses: List[knx_stack.Address], events: "home.Event" = None
    ) -> "knx_plugin.Trigger":
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description, events)
        dsc.addresses = addresses
        return dsc

    @classmethod
    def make_from_yaml(
        cls, addresses: List[int], events: "home.Event" = None
    ) -> "knx_plugin.Trigger":
        description = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(description, events)

    def is_triggered(
        self, another_description: "knx_plugin.message.Description"
    ) -> bool:
        if super(Trigger, self).is_triggered(another_description):
            if set(self.asaps).intersection(set(another_description.asaps)):
                return True
        return False


class Equal(Trigger, home.protocol.Trigger):
    """A trigger triggered when

      1) it has some ASAPs in common with the compared Description and
      2) the knx_stack.datapointtypes.DPT described in the compared Description received from bus is equal
         to the knx_stack.datapointtypes.DPT described by the trigger

    Example::

      >>> import knx_stack
      >>> import knx_plugin
      >>> from knx_stack.datapointtypes import DPT_SceneControl

      >>> trigger = knx_plugin.trigger.dpt_scene_control.Activate.make(
      ...                    addresses=[knx_stack.GroupAddress(free_style=1234)],
      ...                    number=7)
      >>> trigger.dpt.number
      7
      >>> trigger.dpt.command == DPT_SceneControl.Command.activate
      True

      >>> address_table = knx_stack.AddressTable(knx_stack.Address(4097), [], 255)
      >>> association_table = knx_stack.AssociationTable(address_table, [])
      >>> groupobject_table = knx_stack.GroupObjectTable()
      >>> trigger.associate(association_table, groupobject_table)

      >>> from_bus = {"name": "DPT_SceneControl",
      ...             "addresses": [1234],
      ...             "fields": {"number": 1, "command": "activate"}}
      >>> another_description = knx_plugin.Description(from_bus)
      >>> another_description._asaps = [knx_stack.ASAP(1)]
      >>> trigger.is_triggered(another_description)
      False
    """

    def is_triggered(
        self, another_description: "knx_plugin.message.Description"
    ) -> bool:
        if super(Equal, self).is_triggered(another_description):
            triggered = self.dpt.value == another_description.dpt.value
            return triggered

    def __str__(self):
        s = super(Equal, self).__str__()
        return "{} equals {}".format(s, self.dpt)


class Always(Trigger, home.protocol.Trigger, home.protocol.mean.Mixin):
    """A trigger triggered when

    1) it has some ASAPs in common with the compared Description and
    2) the knx_stack.datapointtypes.DPT **type** described in the compared Description received from bus is equal
       to the knx_stack.datapointtypes.DPT **type** described by the trigger
    """

    def is_triggered(
        self, another_description: "knx_plugin.message.Description"
    ) -> bool:
        if super(Always, self).is_triggered(another_description):
            if set(self.asaps) & set(another_description.asaps):
                return True

    def make_new_state_from(
        self,
        another_description: "knx_plugin.message.Description",
        old_state: "home.appliance.State",
    ) -> "home.appliance.State":
        new_state = super(Always, self).make_new_state_from(
            another_description, old_state
        )
        new_state = new_state.next(another_description.dpt.decode())
        return new_state

    def get_value(self, description: "knx_plugin.message.Description") -> float:
        return description.dpt.decode()


class ComparisonMixin:
    @staticmethod
    def override_value(description, value=None):
        if value:
            description["fields"]["decoded_value"] = int(value)
        return description

    @classmethod
    def make_from_yaml(
        cls,
        addresses: List[int],
        events: "home.Event" = None,
        value: int = None,
    ) -> "knx_plugin.Trigger":
        description = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(description, events, value)


class GreaterThan(ComparisonMixin, Trigger, home.protocol.Trigger):
    """A trigger triggered when

      1) it has some ASAPs in common with the compared Description and
      2) the knx_stack.datapointtypes.DPT **int value** contained in the compared Description
         received from bus is lesser than the knx_stack.datapointtypes.DPT **int value**
         contained into the trigger

    Use it when the comparison result has to be immediate otherwise use
    :meth:`knx_plugin.trigger.mean.definition.GreaterThan`
    """

    def __init__(
        self,
        description: "knx_plugin.message.Description",
        events: "home.Event" = None,
        value: int = None,
    ):
        description = self.override_value(description, value)
        super(GreaterThan, self).__init__(description, events)

    def is_triggered(
        self, another_description: "knx_plugin.message.Description"
    ) -> bool:
        if super(GreaterThan, self).is_triggered(another_description):
            if set(self.asaps).intersection(set(another_description.asaps)):
                triggered = self.dpt.decode() < another_description.dpt.decode()
                return triggered

    def __str__(self):
        s = super(GreaterThan, self).__str__()
        return "{} greater than {}".format(s, self.dpt.decode())


class LesserThan(Trigger, home.protocol.Trigger, ComparisonMixin):
    """A trigger triggered when

    1) it has some ASAPs in common with the compared Description and
    2) the knx_stack.datapointtypes.DPT **int value** contained in the compared Description received from bus is greater
       than the knx_stack.datapointtypes.DPT **int value** contained into the trigger
    """

    def __init__(
        self,
        description: "knx_plugin.message.Description",
        events: "home.Event" = None,
        value: int = None,
    ):
        description = self.override_value(description, value)
        super(LesserThan, self).__init__(description, events)

    def is_triggered(self, another_description) -> bool:
        if super(LesserThan, self).is_triggered(another_description):
            if set(self.asaps).intersection(set(another_description.asaps)):
                triggered = self.dpt.decode() > another_description.dpt.decode()
                return triggered

    def __str__(self):
        s = super(LesserThan, self).__str__()
        return "{} lesser than {}".format(s, self.dpt.decode())


class InBetween(Trigger, home.protocol.Trigger, ComparisonMixin):
    """A trigger triggered when

    1) it has some ASAPs in common with the compared Description and
    2) the knx_stack.datapointtypes.DPT **int value** contained in the compared Description received from bus is greater
       than the knx_stack.datapointtypes.DPT **int value** contained into the trigger and lesser than this last value
       plus a **range**
    """

    def __init__(
        self,
        description: "knx_plugin.message.Description",
        events: "home.Event" = None,
        value: int = None,
        range: int = None,
    ):
        description = self.override_value(description, value)
        super(InBetween, self).__init__(description, events)
        self._range = range if range else 1

    def is_triggered(
        self, another_description: "knx_plugin.message.Description"
    ) -> bool:
        if super(InBetween, self).is_triggered(another_description):
            triggered = (
                self.dpt.decode()
                < another_description.dpt.decode()
                < (self.dpt.decode() + self._range)
            )
            return triggered
        return False

    def __str__(self):
        s = super(InBetween, self).__str__()
        return "{} in between [{}:{}]".format(
            s, self.dpt.decode(), (self.dpt.decode() + self._range)
        )


from knx_plugin.trigger import (
    mean,
    custom_clima,
    custom_scene,
    dpt_value_lux,
    dpt_value_power,
    dpt_brightness,
    dpt_switch,
    dpt_updown,
    dpt_value_temp,
    dpt_value_wsp,
    dpt_control_dimming,
    dpt_scene_control,
    dpt_start,
)

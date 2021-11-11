import copy
import collections
import functools

from typing import List

import home
import knx_stack
from knx_plugin.message import Description
from knx_plugin.trigger import Trigger


class Mean(Trigger, home.protocol.Trigger):
    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
    ):
        if value:
            description["fields"]["decoded_value"] = int(value)
        super(Mean, self).__init__(description, events)
        self._samples = collections.deque(maxlen=(samples if samples else 1))
        self._mean = None

    def is_triggered(self, another_description: Description) -> bool:
        if super(Mean, self).is_triggered(another_description):
            if set(self.asaps).intersection(set(another_description.asaps)):
                self._samples.append(another_description.dpt.decode())
                self._mean = functools.reduce(
                    lambda a, b: a + b, self._samples, 0
                ) / len(self._samples)
                return True

    @classmethod
    def make(
        cls,
        addresses: List[knx_stack.Address],
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
    ):
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description, events, samples, value)
        dsc.addresses = addresses
        return dsc

    def __str__(self):
        s = super(Mean, self).__str__()
        return "mean value {} (for {})".format(self._mean, s)


class GreaterThan(Mean):
    """A trigger triggered when

      1) it has some ASAPs in common with the compared Description and
      2) the knx_stack.datapointtypes.DPT **value** contained into the trigger
         is greater than the **mean value** of knx_stack.datapointtypes.DPT **values** received from bus

    The **mean** is calculated using last **num of samples** *Descriptions*.

    Use it when changes has to be slow down otherwise use
    :meth:`knx_plugin.trigger.definition.GreaterThan`.

    More *high* is *num of samples* more slow are changes.
    """

    def is_triggered(self, another_description: Description) -> bool:
        if super(GreaterThan, self).is_triggered(another_description):
            triggered = self.dpt.decode() < self._mean
            return triggered

    def __str__(self):
        s = super(GreaterThan, self).__str__()
        return "{} greater than {}".format(s, self.dpt.decode())


class LesserThan(Mean):
    """A trigger triggered when

      1) it has some ASAPs in common with the compared Description and
      2) the knx_stack.datapointtypes.DPT **value** contained into the trigger
         is lesser than the **mean value** of knx_stack.datapointtypes.DPT **values** received from bus

    The **mean** is calculated using last **num of samples** *Descriptions*.

    Use it when changes has to be slow down otherwise use
    :meth:`knx_plugin.trigger.definition.LesserThan`.

    More *high* is *num of samples* more slow are changes.
    """

    def is_triggered(self, another_description: Description) -> bool:
        if super(LesserThan, self).is_triggered(another_description):
            triggered = self.dpt.decode() > self._mean
            return triggered

    def __str__(self):
        s = super(LesserThan, self).__str__()
        return "{} lesser than {}".format(s, self.dpt.decode())


class InBetween(Mean):
    """A trigger triggered when

      1) it has some ASAPs in common with the compared Description and
      2) the knx_stack.datapointtypes.DPT **value** contained into the trigger
         is greater than the **mean value** of knx_stack.datapointtypes.DPT **values** received from bus
         and lesser than the **mean vlaue** plus a given **range**

    The **mean** is calculated using last **num of samples** *Descriptions*.

    Use it when changes has to be slow down otherwise use
    :meth:`knx_plugin.trigger.definition.InBetween`.

    More *high* is *num of samples* more slow are changes.
    """

    def __init__(
        self,
        description: dict,
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
        range: int = None,
    ):
        super(InBetween, self).__init__(description, events, samples, value)
        self._range = range if range else 1

    def is_triggered(self, another_description: Description) -> bool:
        if super(InBetween, self).is_triggered(another_description):
            triggered = (
                self.dpt.decode() < self._mean < (self.dpt.decode() + self._range)
            )
            return triggered
        return False

    def __str__(self):
        s = super(InBetween, self).__str__()
        return "{} in between [{}:{}]".format(
            s, self.dpt.decode(), (self.dpt.decode() + self._range)
        )

    @classmethod
    def make(
        cls,
        addresses: List[knx_stack.Address],
        events: List[home.Event] = None,
        samples: int = None,
        value: float = None,
        range: int = None,
    ):
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description, events, samples, value, range)
        dsc.addresses = addresses
        return dsc

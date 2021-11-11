import copy
import logging

from typing import List, Union, Type

import home
import knx_stack


class Description(home.protocol.Description):

    PROTOCOL = "knx"

    DPT = {"name": "Fake", "fields": {}}

    def __init__(self, data: dict):
        super(Description, self).__init__(data)
        factory = knx_stack.datapointtypes.DPT_Factory()
        fields = data["fields"] if "fields" in data else {}
        self._dpt: Type[knx_stack.datapointtypes.DPT] = factory.make(
            data["name"], fields
        )
        self._dpt_class = self._dpt.__class__
        self._addresses: List[knx_stack.Address] = (
            [
                knx_stack.GroupAddress(free_style=address)
                for address in data["addresses"]
            ]
            if "addresses" in data
            else []
        )
        self._asaps = []
        self._label = "{} {}".format(self._dpt.__class__.__name__, self._addresses)

        self._logger = logging.getLogger(__name__)

    @property
    def dpt(self) -> Type[knx_stack.datapointtypes.DPT]:
        return self._dpt

    @property
    def asaps(self) -> List[knx_stack.ASAP]:
        return self._asaps

    @property
    def addresses(self) -> List[knx_stack.Address]:
        return self._addresses

    @addresses.setter
    def addresses(self, value: List[knx_stack.Address]):
        self._addresses = value

    @classmethod
    def make(
        cls, addresses: List[knx_stack.Address]
    ) -> "knx_plugin.message.Description":
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description)
        dsc.addresses = addresses
        return dsc

    @classmethod
    def make_from_yaml(cls, addresses: List[int]) -> "knx_plugin.message.Description":
        description = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(description)

    @classmethod
    def make_from(
        cls,
        msg: Union[
            knx_stack.layer.application.a_group_value_read.ind.Msg,
            knx_stack.layer.application.a_group_value_write.ind.Msg,
        ],
    ) -> "knx_plugin.message.Description":
        dpt_description = knx_stack.datapointtypes.Description_Factory.make(msg.dpt)
        description = {
            "type": "knx",
            "name": dpt_description[0],
            "addresses": [],
            "fields": dpt_description[1],
        }
        d = cls(description)
        d._asaps = [knx_stack.ASAP(msg.asap.value, "{}".format(d.label))]
        return d

    def __eq__(self, other):
        if self.PROTOCOL == other.PROTOCOL:
            if self.dpt.__class__ == other.dpt.__class__ and set(
                self.asaps
            ).intersection(set(other.asaps)):
                return True
        return False

    def __hash__(self):
        s = "class: {} asaps: {}".format(
            self.dpt.__class__.__name__, [str(asap.value) for asap in self._asaps]
        )
        return hash(s)

    def associate_with(self, association_table: knx_stack.AssociationTable) -> None:
        for address in self._addresses:
            tsap = association_table.get_tsap(address)
            asaps = association_table.get_asaps(tsap)
            self._asaps.extend(asaps)

    def associate(
        self,
        association_table: knx_stack.AssociationTable,
        groupobject_table: knx_stack.GroupObjectTable,
    ):
        value = association_table.get_free_asap_value()
        asap = knx_stack.ASAP(
            value,
            "{}: {} {}".format(
                self._label, self.dpt.__class__.__name__, self._addresses
            ),
        )
        self._asaps.append(asap)
        association_table.associate(asap, self._addresses)
        groupobject_table.associate(asap, self._dpt_class)

        self._logger.info(
            "associate %s for %s to asap %s"
            % (str(self._addresses), str(self.dpt.__class__.__name__), str(self.asaps))
        )

    def __str__(self, *args, **kwargs):
        return self._label


class Command(Description, home.protocol.Command):
    """A generic KNX command.

    Example:
      >>> import knx_stack
      >>> import knx_plugin

      >>> address_table = knx_stack.AddressTable(knx_stack.Address(4097), [], 255)
      >>> association_table = knx_stack.AssociationTable(address_table, [])
      >>> groupobject_table = knx_stack.GroupObjectTable()

      >>> data = {"name": "DPT_SceneControl",
      ...         "addresses": [2823],
      ...         "fields": {"number": 7, "command": "activate"}}
      >>> class C(knx_plugin.Command):
      ...     def make_msgs_from(self, old_state, new_state):
      ...         pass
      >>> command = C(data)
      >>> command.associate(association_table, groupobject_table)
      >>> msgs = command.execute()
      >>> msgs[0].dpt.number
      7
      >>> msgs[0].dpt.command
      <Command.activate: 0>
    """

    def execute(
        self,
    ) -> List["knx_stack.layer.application.a_group_value_write.req.Msg"]:
        req_msgs = []
        for asap in self._asaps:
            req_msgs.append(
                knx_stack.layer.application.a_group_value_write.req.Msg(
                    asap=asap, dpt=self._dpt
                )
            )
        self._logger.info("executed %s with msgs %s" % (str(self), str(req_msgs)))
        return req_msgs

import asyncio
import logging

from typing import Iterable, Callable, Union

import home
import knx_stack

from knx_plugin.message import Description
from knx_plugin.trigger import Trigger


class Gateway(home.protocol.Gateway):

    PROTOCOL = Description.PROTOCOL

    def __init__(
        self, client: "knx_plugin.Client", host: str = "0.0.0.0", port: int = 5555
    ):
        self._client = client
        self._host = host
        self._port = port
        self._triggers = set()
        self._protocol_instance = None
        self._transport = None

        address_table = knx_stack.AddressTable(knx_stack.Address(0x0000), [], 1000)
        self._association_table = knx_stack.AssociationTable(address_table, [])
        self._datapointtypes = knx_stack.GroupObjectTable()
        self._knx_state = None
        self._init_state()

        self._loop = asyncio.get_event_loop()
        self.logger = logging.getLogger(__name__)

    def _init_state(self):
        raise NotImplementedError

    @property
    def protocol_instance(self):
        return self._protocol_instance

    async def disconnect(self) -> None:
        if self._transport:
            self._transport.close()

    def _associate(self, descriptions):
        for description in descriptions:
            description.associate(self._association_table, self._datapointtypes)

        self.logger.info(self._association_table)
        self.logger.info(self._datapointtypes)

    def associate_commands(self, descriptions: "knx_plugin.message.Command") -> None:
        self._associate(descriptions)

    def associate_triggers(self, descriptions: "knx_plugin.message.Trigger") -> None:
        self._associate(descriptions)

    async def run(self, other_tasks: Iterable[Callable]) -> None:
        while True:
            on_con_lost = self._loop.create_future()
            self._protocol_instance = self._client(
                on_con_lost, self._knx_state, self._wrap_tasks(other_tasks)
            )
            try:
                (self._transport, _) = await self._loop.create_connection(
                    lambda: self._protocol_instance, self._host, self._port
                )
                try:
                    await on_con_lost
                finally:
                    self._transport.close()
            except (TimeoutError, OSError) as e:
                self.logger.fatal(e)
                await asyncio.sleep(60)


    @staticmethod
    def make_trigger(
        msg: Union[
            "knx_stack.layer.application.a_group_value_write.ind.Msg",
            "knx_stack.layer.application.a_group_value_read.ind.Msg",
        ]
    ):
        logger = logging.getLogger(__name__)
        if (
            isinstance(msg, knx_stack.layer.application.a_group_value_write.ind.Msg)
            or isinstance(msg, knx_stack.layer.application.a_group_value_write.ind.Msg)
            or isinstance(msg, knx_stack.layer.application.a_group_value_read.req.Msg)
            or isinstance(msg, knx_stack.layer.application.a_group_value_write.req.Msg)
            or isinstance(msg, knx_stack.layer.application.a_group_value_write.con.Msg)
            or isinstance(msg, knx_stack.layer.application.a_group_value_write.con.Msg)
        ):
            trigger = Trigger.make_from(msg)
            logger.debug("{} for asaps {}".format(trigger.dpt, trigger.asaps))
            return trigger
        elif isinstance(
            msg, knx_stack.decode.knxnet_ip.core.connect.res.Msg
        ) or isinstance(msg, knx_stack.decode.knxnet_ip.tunneling.req.Msg):
            logger.debug("knxnet ip protocol knx message {}".format(msg))
            pass
        else:
            logger.error("Not a managed knx message {}".format(msg))

    async def writer(
        self,
        msgs: Iterable[
            Union[
                "knx_stack.layer.application.a_group_value_write.req.Msg",
                "knx_stack.layer.application.a_group_value_read.req.Msg",
            ]
        ],
        *args
    ):
        while not self._protocol_instance:
            await asyncio.sleep(0.01)
        await self._protocol_instance.write(msgs, *args)


from knx_plugin.gateway import usbhid, knxnet_ip

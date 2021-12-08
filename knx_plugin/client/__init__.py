import asyncio
import logging

import knx_stack
from typing import Iterable, Callable, Union, Tuple, Any


class MsgNotEncoded(Exception):
    """Knx msg has not been encoded"""


class Client(asyncio.Protocol):

    def __init__(self, on_con_lost, knx_state: "knx_stack.State", tasks: Iterable["Callable"]):
        self._loop = asyncio.get_event_loop()
        self._transport = None
        self._tasks = set(tasks)
        self._state = knx_state
        self._on_con_lost = on_con_lost

        self.logger = logging.getLogger(__name__)

    def connection_made(self, transport):
        self._transport = transport
        self.logger.info("Connection made: {}".format(str(self._transport)))

    def connection_lost(self, exc):
        self.logger.error("Connection lost: {}".format(str(exc)))
        self._on_con_lost.set_result(True)
        self._transport = None

    def error_received(self, exc):
        self.logger.error("Error received: {}".format(str(exc)))

    def encode(
        self,
        msg: Union[
            "knx_stack.layer.application.a_group_value_write.req.Msg",
            "knx_stack.layer.application.a_group_value_write.req.Msg",
            "knx_stack.layer.application.a_group_value_write.ind.Msg",
        ],
    ) -> "knx_stack.Msg":
        if isinstance(msg, knx_stack.layer.application.a_group_value_write.req.Msg):
            knx_msg = knx_stack.encode_msg(self._state, msg)
        elif isinstance(msg, knx_stack.layer.application.a_group_value_read.req.Msg):
            knx_msg = knx_stack.encode_msg(self._state, msg)
        elif isinstance(msg, knx_stack.layer.application.a_group_value_write.ind.Msg):
            knx_msg = knx_stack.encode_msg(self._state, msg)
        else:
            raise MsgNotEncoded("msg: {} could not be encoded".format(msg))

        return knx_msg

    def filter(
        self,
        msgs: Iterable[
            Union[
                "knx_stack.layer.application.a_group_value_read.req.Msg",
                "knx_stack.layer.application.a_group_value_write.req.Msg",
                "knx_stack.layer.application.a_group_value_read.con.Msg",
                "knx_stack.layer.application.a_group_value_write.con.Msg",
                "knx_stack.layer.application.a_group_value_read.ind.Msg",
                "knx_stack.layer.application.a_group_value_write.ind.Msg",
            ]
        ],
    ) -> Tuple[
        Iterable[
            Union[
                "knx_stack.layer.application.a_group_value_read.req.Msg",
                "knx_stack.layer.application.a_group_value_write.req.Msg",
            ]
        ],
        Iterable[
            Union[
                "knx_stack.layer.application.a_group_value_read.con.Msg",
                "knx_stack.layer.application.a_group_value_write.con.Msg",
            ]
        ],
        Iterable[
            Union[
                "knx_stack.layer.application.a_group_value_read.ind.Msg",
                "knx_stack.layer.application.a_group_value_write.ind.Msg",
            ]
        ],
        Iterable[Any],
    ]:
        req = list()
        con = list()
        ind = list()
        others = list()
        if msgs:
            for msg in msgs:
                if isinstance(
                    msg, knx_stack.layer.application.a_group_value_read.req.Msg
                ) or isinstance(
                    msg, knx_stack.layer.application.a_group_value_write.req.Msg
                ):
                    req.append(msg)
                elif isinstance(
                    msg, knx_stack.layer.application.a_group_value_read.con.Msg
                ) or isinstance(
                    msg, knx_stack.layer.application.a_group_value_write.con.Msg
                ):
                    con.append(msg)
                elif isinstance(
                    msg, knx_stack.layer.application.a_group_value_read.ind.Msg
                ) or isinstance(
                    msg, knx_stack.layer.application.a_group_value_write.ind.Msg
                ):
                    ind.append(msg)
                else:
                    others.append(msg)
        return req, con, ind, others

    async def _wait_for_transport(self):
        while not self._transport:
            await asyncio.sleep(0.1)

    async def write(self, msgs, *args):
        raise NotImplementedError


from knx_plugin.client import knxnet_ip, usbhid

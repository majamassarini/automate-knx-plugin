import datetime
import asyncio

import knx_stack
from typing import Iterable, Callable
from knx_plugin.client import Client as Parent


class KnxnetIPClientException(Exception):
    pass


class Client(Parent):

    MAX_RETRIES = 3

    def __init__(
        self,
        on_con_close,
        knx_state: "knx_stack.State",
        tasks: Iterable["Callable"],
        local_addr: str,
        local_port: int,
        remote_addr: str,
        remote_port: int,
    ):
        super(Client, self).__init__(on_con_close, knx_state, tasks)
        self._local_addr = local_addr
        self._local_port = local_port
        self._remote_addr = remote_addr
        self._remote_port = remote_port
        self._connect_timeout = None
        self._tunneling_request_timeout = None
        self._connect_alive_timeout = None
        self._retries = 0
        self._got_a_confirmation = False

    def connection_made(self, transport):
        super(Client, self).connection_made(transport)
        connect_req = knx_stack.knxnet_ip.core.connect.req.Msg(
            addr_control_endpoint=self._local_addr,
            port_control_endpoint=self._local_port,
            addr_data_endpoint=self._local_addr,
            port_data_endpoint=self._local_port,
        )
        self._loop.create_task(self.manage_connect_timeout())
        msg = knx_stack.encode_msg(self._state, connect_req)
        self._transport.sendto(self.encode(msg), (self._remote_addr, self._remote_port))
        self._connect_timeout = datetime.datetime.now()

    def decode(self, data):
        msgs = []
        msg = knx_stack.knxnet_ip.Msg.make_from_str(data.hex())
        self.logger.debug("received: {}".format(msg))
        try:
            msgs = knx_stack.decode_msg(self._state, msg)
        except TypeError as e:
            self.logger.error(e)
        return msgs

    def encode(self, msg):
        self.logger.debug("sent: {}".format(msg))
        final_msg = bytearray.fromhex(str(msg))
        return final_msg

    def datagram_received(self, data, addr):
        msgs = self.decode(data)
        (reqs, cons, inds, others) = self.filter(msgs)
        for task in self._tasks:
            for con in cons:
                self._loop.create_task(task(con))
            for ind in inds:
                self._loop.create_task(task(ind))
            for con in cons:
                self.manage_request_confirmation(con)
            for other in others:
                self.manage_connect(other)
                self.manage_server_tunneling_request(other)

    async def write(self, msgs, *args):
        await self._wait_for_transport()
        for msg in msgs:
            if isinstance(msg, knx_stack.layer.application.a_group_value_write.req.Msg):
                while self._retries < self.MAX_RETRIES and not self._got_a_confirmation:
                    self.logger.info("retry {}".format(self._retries))
                    self._retries += 1
                    self._got_a_confirmation = False
                    req = knx_stack.encode_msg(self._state, msg)
                    self._transport.sendto(
                        self.encode(req), (self._remote_addr, self._remote_port)
                    )
                    self._tunneling_request_timeout = datetime.datetime.now()
                    await self.manage_tunneling_request_timeout()
                self._retries = 0
                self._got_a_confirmation = False

    def manage_connect(self, msg):
        if self._connect_timeout:
            self.logger.info("{}".format(msg))
            if isinstance(msg, knx_stack.knxnet_ip.core.connect.res.Msg):
                self.logger.info("ConnectRes received")
                if msg.status == knx_stack.knxnet_ip.ErrorCodes.E_NO_ERROR:
                    self._connect_alive_timeout = datetime.datetime.now()
                    self._loop.create_task(self.manage_connect_alive_timeout())
                    self.logger.info("Knxnet ip client connected")
                else:
                    raise KnxnetIPClientException(
                        "Knxnet_ip client connection with server {} has an error {}".format(
                            (self._remote_addr, self._local_port),
                            knx_stack.knxnet_ip.ErrorCodes[msg.status],
                        )
                    )

    def manage_request_confirmation(self, msg):
        if self._tunneling_request_timeout:
            if isinstance(msg, knx_stack.layer.application.a_group_value_write.con.Msg):
                self.logger.info("Got a confirmation {}".format(msg))
                self._got_a_confirmation = True

    def manage_server_tunneling_request(self, msg):
        if isinstance(msg, knx_stack.decode.knxnet_ip.tunneling.req.Msg):
            if msg.status == knx_stack.knxnet_ip.ErrorCodes.E_NO_ERROR:
                ack_msg = knx_stack.knxnet_ip.tunneling.ack.Msg(
                    sequence_counter=msg.sequence_counter, status=msg.status
                )
                ack = knx_stack.encode_msg(self._state, ack_msg)
                self._transport.sendto(
                    self.encode(ack), (self._remote_addr, self._remote_port)
                )
                self._connect_alive_timeout = datetime.datetime.now()
            else:
                self.logger.error(
                    "Received server tunneling request with error {}".format(
                        knx_stack.definition.knxnet_ip.ErrorCodes(msg.status)
                    )
                )

    async def manage_connect_timeout(self):
        while True:
            try:
                if self._connect_timeout:
                    if (
                        datetime.datetime.now() - self._connect_timeout
                    ) > datetime.timedelta(
                        seconds=knx_stack.knxnet_ip.CONNECT_REQUEST_TIMEOUT
                    ):
                        self.logger.info("Connect timeout expired")
                        self._connect_timeout = None
                        break
                await asyncio.sleep(knx_stack.knxnet_ip.CONNECT_REQUEST_TIMEOUT / 3)
            except Exception as e:
                self.logger.error(e)

    async def manage_tunneling_request_timeout(self):
        while True:
            try:
                if self._tunneling_request_timeout:
                    if (
                        datetime.datetime.now() - self._tunneling_request_timeout
                    ) > datetime.timedelta(
                        seconds=knx_stack.knxnet_ip.TUNNELING_REQUEST_TIMEOUT
                    ):
                        self.logger.info("Tunneling request timeout expired")
                        self._tunneling_request_timeout = None
                        break
                    elif self._got_a_confirmation:
                        self._tunneling_request_timeout = None
                        break
                    else:
                        self.logger.info("Tunneling request timeout not expired yet")
                        await asyncio.sleep(
                            knx_stack.knxnet_ip.TUNNELING_REQUEST_TIMEOUT / 6
                        )
                elif self._got_a_confirmation:
                    self._tunneling_request_timeout = None
                    break
                else:
                    await asyncio.sleep(
                        knx_stack.knxnet_ip.TUNNELING_REQUEST_TIMEOUT / 4
                    )
            except Exception as e:
                self.logger.error(e)

    async def manage_connect_alive_timeout(self):
        while True:
            try:
                if self._connect_alive_timeout:
                    if (
                        datetime.datetime.now() - self._connect_alive_timeout
                    ) > datetime.timedelta(
                        seconds=(knx_stack.knxnet_ip.CONNECTION_ALIVE_TIME / 2)
                    ):
                        self.logger.info("Connect alive timeout expired")
                        req_msg = knx_stack.knxnet_ip.core.connectionstate.req.Msg(
                            addr_control_endpoint=self._local_addr,
                            port_control_endpoint=self._local_port,
                        )
                        knx_msg = knx_stack.encode_msg(self._state, req_msg)
                        self._connect_alive_timeout = datetime.datetime.now()
                        self._transport.sendto(
                            self.encode(knx_msg), (self._remote_addr, self._remote_port)
                        )
                await asyncio.sleep(knx_stack.knxnet_ip.CONNECTION_ALIVE_TIME / 2)
            except Exception as e:
                self.logger.error(e)

    async def disconnect(self):
        disconnect_req = knx_stack.knxnet_ip.core.disconnect.req.Msg(
            addr_control_endpoint=self._local_addr,
            port_control_endpoint=self._local_port,
        )
        msg = knx_stack.encode_msg(self._state, disconnect_req)
        self._transport.sendto(self.encode(msg), (self._remote_addr, self._remote_port))

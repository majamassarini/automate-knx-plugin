import datetime
import asyncio

import knx_stack
from collections.abc import Callable, Iterable
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
        nat_local_addr: str,
        nat_local_port: int,
        local_addr: str,
        local_port: int,
        remote_addr: str,
        remote_port: int,
    ):
        super(Client, self).__init__(on_con_close, knx_state, tasks)
        self._nat_local_addr = nat_local_addr
        self._nat_local_port = nat_local_port
        self._local_addr = local_addr
        self._local_port = local_port
        self._remote_addr = remote_addr
        self._remote_port = remote_port
        self._connect_timeout = None
        self._tunneling_request_timeout = None
        self._connect_alive_timeout = None
        self._connect_alive_response_timeout = None
        self._retries = 0
        self._got_a_confirmation = False
        self._got_alive_response = False
        self._missed_keepalives = 0
        self.MAX_MISSED_KEEPALIVES = 3

        # Exponential backoff for reconnection
        self._reconnect_attempt = 0
        self._max_reconnect_attempts = 10
        self._base_reconnect_delay = 1  # Start with 1 second
        self._max_reconnect_delay = 300  # Cap at 5 minutes
        self._last_connection_success = None
        self._reconnect_task = None

    def connection_made(self, transport):
        super(Client, self).connection_made(transport)
        # Reset state for new connection
        self._state.communication_channel_id = 0
        self._state.sequence_counter_local = 0
        self._state.sequence_counter_remote = 0
        self._missed_keepalives = 0
        self._got_a_confirmation = False
        self._got_alive_response = False
        self._retries = 0

        # Reset reconnection backoff on successful connection
        self._reconnect_attempt = 0
        self._last_connection_success = datetime.datetime.now()

        connect_req = knx_stack.knxnet_ip.core.connect.req.Msg(
            addr_control_endpoint=self._local_addr,
            port_control_endpoint=self._local_port,
            addr_data_endpoint=self._local_addr,
            port_data_endpoint=self._local_port,
        )
        asyncio.get_running_loop().create_task(self.manage_connect_timeout())
        msg = knx_stack.encode_msg(self._state, connect_req)
        self._transport.sendto(
            self.encode(msg), (self._remote_addr, self._remote_port)
        )
        self._connect_timeout = datetime.datetime.now()

    def decode(self, data):
        msgs = []
        try:
            msg = knx_stack.knxnet_ip.Msg.make_from_str(data.hex())
            self.logger.debug("received: {}".format(msg))
            msgs = knx_stack.decode_msg(self._state, msg)
        except TypeError as e:
            # Enhanced logging for HPAI parsing errors
            self.logger.error("Failed to decode message: {}".format(e))
            self.logger.error(
                "Message decode failure details:\n"
                "  Error type: TypeError\n"
                "  Data length: {} bytes\n"
                "  Hex dump: {}\n"
                "  ASCII (errors='replace'): {}".format(
                    len(data),
                    data.hex(),
                    data.decode("ascii", errors="replace"),
                )
            )
            # Check if it looks like a malformed HPAI
            if b"HPAI" in str(e) or "No HPAI message" in str(e):
                self.logger.warning(
                    "HPAI parsing error detected - possible protocol mismatch or corruption"
                )
        except Exception as e:
            self.logger.error(
                "Unexpected error decoding message: {}".format(e)
            )
            self.logger.error(
                "Unexpected decode failure details:\n"
                "  Error type: {}\n"
                "  Data length: {} bytes\n"
                "  Hex dump: {}\n"
                "  ASCII (errors='replace'): {}".format(
                    type(e).__name__,
                    len(data),
                    data.hex(),
                    data.decode("ascii", errors="replace"),
                )
            )
        return msgs

    def encode(self, msg):
        self.logger.debug("sent: {}".format(msg))
        final_msg = bytearray.fromhex(str(msg))
        return final_msg

    def datagram_received(self, data, addr):
        msgs = self.decode(data)
        reqs, cons, inds, others = self.filter(msgs)
        for task in self._tasks:
            for con in cons:
                asyncio.get_running_loop().create_task(task(con))
            for ind in inds:
                asyncio.get_running_loop().create_task(task(ind))
            for con in cons:
                self.manage_request_confirmation(con)
            for other in others:
                self.manage_connect(other)
                self.manage_server_tunneling_request(other)
                self.manage_disconnect_request(other)

    async def write(self, msgs, *args):
        await self._wait_for_transport()
        for msg in msgs:
            if isinstance(
                msg, knx_stack.layer.application.a_group_value_write.req.Msg
            ):
                while (
                    self._retries < self.MAX_RETRIES
                    and not self._got_a_confirmation
                ):
                    self.logger.info("retry {}".format(self._retries))
                    self._retries += 1
                    self._got_a_confirmation = False
                    req = knx_stack.encode_msg(self._state, msg)
                    self._transport.sendto(
                        self.encode(req),
                        (self._remote_addr, self._remote_port),
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
                    asyncio.get_running_loop().create_task(
                        self.manage_connect_alive_timeout()
                    )

                    # Connection successful - reset reconnection backoff
                    if self._reconnect_attempt > 0:
                        self.logger.info(
                            "Connection restored after {} reconnection attempts".format(
                                self._reconnect_attempt
                            )
                        )
                    self._reconnect_attempt = 0
                    self._last_connection_success = datetime.datetime.now()

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
            if isinstance(
                msg, knx_stack.layer.application.a_group_value_write.con.Msg
            ):
                self.logger.info("Got a confirmation {}".format(msg))
                self._got_a_confirmation = True

    def manage_server_tunneling_request(self, msg):
        if isinstance(msg, knx_stack.decode.knxnet_ip.tunneling.req.Msg):
            # Always send ACK, even if there's an error
            ack_msg = knx_stack.knxnet_ip.tunneling.ack.Msg(
                sequence_counter=msg.sequence_counter, status=msg.status
            )
            ack = knx_stack.encode_msg(self._state, ack_msg)
            self._transport.sendto(
                self.encode(ack), (self._remote_addr, self._remote_port)
            )

            if msg.status == knx_stack.knxnet_ip.ErrorCodes.E_NO_ERROR:
                self._connect_alive_timeout = datetime.datetime.now()
            else:
                error_code = knx_stack.definition.knxnet_ip.ErrorCodes(
                    msg.status
                )
                self.logger.error(
                    "Received server tunneling request with error {}".format(
                        error_code
                    )
                )
                # Error 3 typically means E_CONNECTION_ID - server doesn't recognize our connection
                # We need a full reconnection with exponential backoff
                if (
                    msg.status == 3
                    or msg.status
                    == knx_stack.knxnet_ip.ErrorCodes.E_SEQUENCE_NUMBER
                ):
                    self.logger.warning(
                        "Connection error (code: {}) - scheduling reconnection with backoff".format(
                            msg.status
                        )
                    )
                    # Schedule reconnection with exponential backoff
                    if self._transport:
                        asyncio.get_running_loop().create_task(
                            self._reconnect_with_backoff()
                        )
        elif isinstance(msg, knx_stack.knxnet_ip.core.connectionstate.res.Msg):
            # Received response to our keepalive request
            self.logger.info(
                "Received connectionstate response: {}".format(msg)
            )
            if msg.status == knx_stack.knxnet_ip.ErrorCodes.E_NO_ERROR:
                self._got_alive_response = True
                self._missed_keepalives = 0
                self._connect_alive_response_timeout = None
                self.logger.debug(
                    "Keepalive acknowledged, connection is healthy"
                )
            else:
                self.logger.error(
                    "Received connectionstate response with error {}".format(
                        knx_stack.definition.knxnet_ip.ErrorCodes(msg.status)
                    )
                )

    def manage_disconnect_request(self, msg):
        if isinstance(msg, knx_stack.knxnet_ip.core.disconnect.req.Msg):
            self.logger.warning(
                "Received disconnect request from gateway: {}".format(msg)
            )
            # Send disconnect response
            disconnect_res = knx_stack.knxnet_ip.core.disconnect.res.Msg(
                communication_channel_id=self._state.communication_channel_id,
                status=knx_stack.knxnet_ip.ErrorCodes.E_NO_ERROR,
            )
            res_msg = knx_stack.encode_msg(self._state, disconnect_res)
            self._transport.sendto(
                self.encode(res_msg), (self._remote_addr, self._remote_port)
            )
            self.logger.info("Sent disconnect response, closing connection")
            # Close transport to trigger reconnection
            if self._transport:
                self._transport.close()

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
                await asyncio.sleep(
                    knx_stack.knxnet_ip.CONNECT_REQUEST_TIMEOUT / 3
                )
            except Exception as e:
                self.logger.error(e)

    async def manage_tunneling_request_timeout(self):
        while True:
            try:
                if self._tunneling_request_timeout:
                    if (
                        datetime.datetime.now()
                        - self._tunneling_request_timeout
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
                        self.logger.info(
                            "Tunneling request timeout not expired yet"
                        )
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
                # Check if we're waiting for a keepalive response
                if self._connect_alive_response_timeout:
                    if (
                        datetime.datetime.now()
                        - self._connect_alive_response_timeout
                    ) > datetime.timedelta(seconds=10):
                        # No response received within 10 seconds
                        if not self._got_alive_response:
                            self._missed_keepalives += 1
                            self.logger.warning(
                                "Missed keepalive response (count: {}/{})".format(
                                    self._missed_keepalives,
                                    self.MAX_MISSED_KEEPALIVES,
                                )
                            )
                            if (
                                self._missed_keepalives
                                >= self.MAX_MISSED_KEEPALIVES
                            ):
                                self.logger.error(
                                    "Too many missed keepalives, scheduling reconnection with backoff"
                                )
                                # Schedule reconnection with exponential backoff
                                if self._transport:
                                    asyncio.get_running_loop().create_task(
                                        self._reconnect_with_backoff()
                                    )
                                break
                        self._connect_alive_response_timeout = None
                        self._got_alive_response = False

                # Check if it's time to send a new keepalive
                if self._connect_alive_timeout:
                    if (
                        datetime.datetime.now() - self._connect_alive_timeout
                    ) > datetime.timedelta(
                        seconds=(knx_stack.knxnet_ip.CONNECTION_ALIVE_TIME / 2)
                    ):
                        self.logger.info(
                            "Sending keepalive (connectionstate request)"
                        )
                        req_msg = (
                            knx_stack.knxnet_ip.core.connectionstate.req.Msg(
                                addr_control_endpoint=self._local_addr,
                                port_control_endpoint=self._local_port,
                            )
                        )
                        knx_msg = knx_stack.encode_msg(self._state, req_msg)
                        self._connect_alive_timeout = datetime.datetime.now()
                        self._connect_alive_response_timeout = (
                            datetime.datetime.now()
                        )
                        self._got_alive_response = False
                        if self._transport:
                            self._transport.sendto(
                                self.encode(knx_msg),
                                (self._remote_addr, self._remote_port),
                            )
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                self.logger.error(
                    "Error in manage_connect_alive_timeout: {}".format(e)
                )
                break

    async def _reconnect_with_backoff(self):
        """
        Implements exponential backoff for reconnections.
        Delays: 1s, 2s, 4s, 8s, 16s, 32s, 64s, 128s, 256s, 300s (max)
        """
        if self._reconnect_task and not self._reconnect_task.done():
            self.logger.debug("Reconnection already in progress, skipping")
            return

        self._reconnect_task = asyncio.current_task()

        # Calculate delay with exponential backoff
        delay = min(
            self._base_reconnect_delay * (2**self._reconnect_attempt),
            self._max_reconnect_delay,
        )

        self._reconnect_attempt += 1

        if self._reconnect_attempt > self._max_reconnect_attempts:
            self.logger.critical(
                "Maximum reconnection attempts ({}) reached - giving up".format(
                    self._max_reconnect_attempts
                )
            )
            # Close transport permanently
            if self._transport:
                self._transport.close()
            return

        self.logger.warning(
            "Reconnection attempt {}/{} - waiting {}s before reconnecting".format(
                self._reconnect_attempt, self._max_reconnect_attempts, delay
            )
        )

        # Wait for backoff delay
        await asyncio.sleep(delay)

        # Send disconnect request to cleanly terminate old connection on server
        # This prevents sequence number mismatches when reconnecting
        if (
            self._transport
            and self._state
            and self._state.communication_channel_id is not None
        ):
            try:
                self.logger.info(
                    "Sending disconnect request before reconnection"
                )
                await self.disconnect()
                # Give server time to process disconnect
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.warning(
                    "Failed to send disconnect request: {}".format(e)
                )

        # Close current transport (if still open) to trigger reconnection
        if self._transport:
            self.logger.info("Closing transport to trigger reconnection")
            self._transport.close()

        self._reconnect_task = None

    async def disconnect(self):
        disconnect_req = knx_stack.knxnet_ip.core.disconnect.req.Msg(
            addr_control_endpoint=self._local_addr,
            port_control_endpoint=self._local_port,
        )
        msg = knx_stack.encode_msg(self._state, disconnect_req)
        self._transport.sendto(
            self.encode(msg), (self._remote_addr, self._remote_port)
        )

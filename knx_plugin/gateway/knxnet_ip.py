import asyncio
import knx_stack
from knx_plugin.gateway import Gateway as Parent


class Gateway(Parent):
    def __init__(
        self,
        client,
        remote_host,
        remote_port,
        local_host,
        local_port,
        nat_local_host,
        nat_local_port,
    ):
        super(Gateway, self).__init__(client, remote_host, remote_port)
        self._local_host = local_host
        self._local_port = local_port
        self._nat_local_host = nat_local_host
        self._nat_local_port = nat_local_port
        self._reconnect_delay = 5  # Initial reconnection delay in seconds
        self._max_reconnect_delay = (
            60  # Maximum delay between reconnection attempts
        )

    def _init_state(self):
        self._knx_state = knx_stack.knxnet_ip.State(
            knx_stack.Medium.knxnet_ip,
            self._association_table,
            self._datapointtypes,
        )

    async def run(self, other_tasks):
        loop = asyncio.get_running_loop()
        while True:
            on_con_lost = loop.create_future()
            self._protocol_instance = self._client(
                on_con_lost,
                self._knx_state,
                self._wrap_tasks(other_tasks),
                self._nat_local_host,
                self._nat_local_port,
                self._local_host,
                self._local_port,
                self._host,
                self._port,
            )
            try:
                self.logger.info(
                    "Connecting to KNX gateway at {}:{}".format(
                        self._host, self._port
                    )
                )
                self._transport, _ = await loop.create_datagram_endpoint(
                    lambda: self._protocol_instance,
                    local_addr=(self._nat_local_host, self._nat_local_port),
                )
                # Connection successful, reset reconnect delay
                self._reconnect_delay = 5
                self.logger.info("Successfully connected to KNX gateway")
                try:
                    await on_con_lost
                    self.logger.warning(
                        "Connection lost, will attempt to reconnect in {} seconds".format(
                            self._reconnect_delay
                        )
                    )
                finally:
                    self._transport.close()
            except (TimeoutError, OSError) as e:
                self.logger.error(
                    "Connection error: {}. Reconnecting in {} seconds".format(
                        e, self._reconnect_delay
                    )
                )

            # Wait before reconnecting with exponential backoff
            await asyncio.sleep(self._reconnect_delay)
            # Increase delay for next attempt, up to max
            self._reconnect_delay = min(
                self._reconnect_delay * 2, self._max_reconnect_delay
            )

    async def disconnect(self):
        await self._protocol_instance.disconnect()
        await super(Gateway, self).disconnect()

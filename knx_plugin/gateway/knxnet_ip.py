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

    def _init_state(self):
        self._knx_state = knx_stack.knxnet_ip.State(
            knx_stack.Medium.knxnet_ip, self._association_table, self._datapointtypes
        )

    async def run(self, other_tasks):
        while True:
            on_con_lost = self._loop.create_future()
            self._protocol_instance = self._client(
                on_con_lost,
                self._knx_state,
                self._wrap_tasks(other_tasks),
                self._nat_local_host,
                self._nat_local_port,
                self._host,
                self._port,
            )
            try:
                (self._transport, _) = await self._loop.create_datagram_endpoint(
                    lambda: self._protocol_instance,
                    local_addr=(self._local_host, self._local_port),
                    remote_addr=(self._host, self._port),
                )
                try:
                    await on_con_lost
                finally:
                    self._transport.close()
            except (TimeoutError, OSError) as e:
                self.logger.fatal(e)
                await asyncio.sleep(60)

    async def disconnect(self):
        await self._protocol_instance.disconnect()
        await super(Gateway, self).disconnect()

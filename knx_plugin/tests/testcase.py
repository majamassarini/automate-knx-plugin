from unittest.mock import AsyncMock

import knx_plugin
from home.tests.testcase import TestCase as Parent


class TestCase(Parent):
    def setUp(self):
        super(TestCase, self).setUp()

    async def write_side_effect(self, msgs, *args):
        pass

    def add_knx_gateway(self, myhome):
        client = knx_plugin.client.usbhid.Client
        self._old_knx_client_write = client.write
        client.write = AsyncMock(side_effect=self.write_side_effect)
        self._knx_gateway = knx_plugin.gateway.usbhid.Gateway(client)
        self._knx_gateway._loop.create_connection = AsyncMock(return_value=(None, None))
        self._knx_gateway.associate_commands(myhome.commands_by("knx"))
        self._knx_gateway.associate_triggers(myhome.triggers_by("knx"))
        self.process.add(self._knx_gateway)

    @property
    def knx_gateway(self):
        return self._knx_gateway

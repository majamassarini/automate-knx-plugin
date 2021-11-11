# SPDX-License-Identifier: GPL-3.0-only
#
# automate home devices
#
# Copyright (C) 2021  Maja Massarini

import asyncio
import unittest
import unittest.mock

import knx_stack
import knx_plugin


class TestGateway(unittest.TestCase):
    def test_stopped(tc):
        description = {
            "name": "DPT_Switch",
            "fields": {"action": "on"},
            "addresses": [1111],
        }
        trigger = knx_plugin.trigger.dpt_switch.On(description)
        command = knx_plugin.command.dpt_switch.OnOff(description)
        events = []

        class Test(unittest.IsolatedAsyncioTestCase):

            STATE_CHANGED = "stopped"
            MAX_LOOP = 10

            async def a_task(self, msgs):
                print(msgs)
                events.append(self.STATE_CHANGED)

            async def postpone_gw_running(self):
                await asyncio.sleep(0.1)
                await self._gateway.run([self.a_task])

            async def asyncSetUp(self):
                self._gateway = knx_plugin.gateway.usbhid.Gateway(
                    knx_plugin.client.usbhid.Client
                )
                self._gateway.associate_triggers([trigger])
                self._gateway._loop.create_connection = unittest.mock.AsyncMock(
                    return_value=(1, None)
                )

                loop = asyncio.get_event_loop()
                loop.create_task(self.postpone_gw_running())
                loop.create_task(self.emulate_bus_event())

                msgs = command.execute()
                loop.create_task(self._gateway.writer([msgs]))

            async def emulate_bus_event(self):
                for asap in trigger.asaps:
                    await asyncio.sleep(0.2)
                    msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                        asap=asap, dpt=trigger.dpt
                    )
                    msg = self._gateway.protocol_instance.encode(msg)
                    self._gateway.protocol_instance.data_received(msg.encode("utf-8"))

            async def test_stopped(self):
                i = 0
                while self.STATE_CHANGED not in events and i < self.MAX_LOOP:
                    await asyncio.sleep(1)
                    i += 1

        test = Test("test_stopped")
        test.run()
        tc.assertIn(Test.STATE_CHANGED, events)

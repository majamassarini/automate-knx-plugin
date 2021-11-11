import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    class Dimmerrr(home.appliance.light.indoor.dimmerable.Appliance):
        def __init__(self, name, events):
            super(Stub.Dimmerrr, self).__init__(name, events)
            self._wait_for_n_updates = 0

        def update_by(self, trigger, description):
            self._wait_for_n_updates += 1
            if self._wait_for_n_updates >= 8:
                asyncio.get_event_loop().stop()
            return super(Stub.Dimmerrr, self).update_by(trigger, description)

    def _build_appliances(self):
        luce = Stub.Dimmerrr("una luce", [])
        collection = home.appliance.Collection()
        collection["luci"] = set(
            [
                luce,
            ]
        )
        return collection

    def _build_performers(self):
        appliance = self.appliances.find("una luce")
        knx_command = knx_plugin.command.dpt_brightness.Brightness.make_from_yaml(
            [
                0xBBBB,
            ]
        )
        knx_trigger_on = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
            [0xCCCC, 0xDDDD], [home.appliance.light.event.forced.Event.On]
        )
        knx_trigger_off = knx_plugin.trigger.dpt_switch.Off.make_from_yaml(
            [0xCCCC, 0xDDDD], [home.appliance.light.event.forced.Event.Off]
        )
        knx_trigger = knx_plugin.trigger.dpt_brightness.Always.make_from_yaml(
            [
                0xBBBB,
            ]
        )
        luce_performer = home.Performer(
            appliance.name,
            appliance,
            [
                knx_command,
            ],
            [
                knx_trigger_on,
                knx_trigger_off,
                knx_trigger,
            ],
        )
        return [luce_performer]

    def _build_group_of_performers(self):
        return {"luci": self._performers}

    def _build_scheduler_triggers(self):
        return []

    def _build_schedule_infos(self):
        return []


class TestLogics(TestCase):
    def test_performer_update(tc):
        tc.enable_logging()
        tc.myhome = Stub()
        tc.make_process(tc.myhome)

        class Test(unittest.IsolatedAsyncioTestCase):

            MAX_LOOP = 10

            async def asyncSetUp(self):
                tc.add_knx_gateway(tc.myhome)
                self._loop = asyncio.get_event_loop()
                tc.create_tasks(self._loop, tc.myhome)
                self._loop.create_task(self.emulate_bus_events())

            async def test_state(self):
                i = 0
                is_notified = False
                while not is_notified and i < self.MAX_LOOP:
                    await asyncio.sleep(0.3)
                    is_notified = tc.myhome.appliances.find("una luce").is_notified(
                        home.appliance.light.event.brightness.Event(44)
                    )
                    i += 1

            async def emulate_bus_events(self):
                await asyncio.sleep(0.1)
                dpt_switch = knx_stack.datapointtypes.DPT_Switch()
                dpt_switch.action = "on"
                dpt_brightness = knx_stack.datapointtypes.DPT_Brightness()
                dpt_brightness.value = 44

                tsap = tc.knx_gateway._association_table.get_tsap(
                    knx_stack.GroupAddress(free_style=0xDDDD)
                )
                asaps = tc.knx_gateway._association_table.get_asaps(tsap)
                for asap in asaps:
                    msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                        asap=asap, dpt=dpt_switch
                    )
                    msg = tc._knx_gateway.protocol_instance.encode(msg)
                    tc._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
                    await asyncio.sleep(0.1)

                tsap = tc.knx_gateway._association_table.get_tsap(
                    knx_stack.GroupAddress(free_style=0xBBBB)
                )
                asaps = tc.knx_gateway._association_table.get_asaps(tsap)
                for asap in asaps:
                    msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                        asap=asap, dpt=dpt_brightness
                    )
                    msg = tc._knx_gateway.protocol_instance.encode(msg)
                    tc._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
                    await asyncio.sleep(0.1)

        test = Test("test_state")
        tc.assertFalse(
            tc.myhome.appliances.find("una luce").is_notified(
                home.appliance.light.event.brightness.Event(44)
            )
        )
        test.run()
        tc.assertTrue(
            tc.myhome.appliances.find("una luce").is_notified(
                home.appliance.light.event.brightness.Event(44)
            )
        )

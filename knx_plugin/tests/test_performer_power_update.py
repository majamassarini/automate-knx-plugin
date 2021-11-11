import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    class Powerrr(home.appliance.sensor.powermeter.Appliance):
        def update_by(self, trigger, description):
            asyncio.get_event_loop().stop()
            return super(Stub.Powerrr, self).update_by(trigger, description)

    def _build_appliances(self):
        sensore = Stub.Powerrr("un sensore", [])
        collection = home.appliance.Collection()
        collection["sensori"] = set(
            [
                sensore,
            ]
        )
        return collection

    def _build_performers(self):
        appliance = self.appliances.find("un sensore")
        knx_trigger = knx_plugin.trigger.dpt_value_power.Always.make_from_yaml(
            [
                0x178D,
            ]
        )
        sensore_performer = home.Performer(
            appliance.name,
            appliance,
            [],
            [
                knx_trigger,
            ],
        )
        return [sensore_performer]

    def _build_group_of_performers(self):
        return {"sensori": self.performers}

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
                    is_notified = tc.myhome.appliances.find("un sensore").is_notified(
                        496.0
                    )
                    i += 1

            async def emulate_bus_events(self):
                await asyncio.sleep(0.1)
                dpt = knx_stack.datapointtypes.DPT_Value_Power()
                dpt.encode(496)

                tsap = tc.knx_gateway._association_table.get_tsap(
                    knx_stack.GroupAddress(0x178D)
                )
                asaps = tc.knx_gateway._association_table.get_asaps(tsap)
                for asap in asaps:
                    msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                        asap=asap, dpt=dpt
                    )
                    msg = tc._knx_gateway.protocol_instance.encode(msg)
                    tc._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
                    await asyncio.sleep(0.1)

        test = Test("test_state")
        tc.assertFalse(tc.myhome.appliances.find("un sensore").is_notified(496.0))
        test.run()
        tc.assertTrue(tc.myhome.appliances.find("un sensore").is_notified(496.0))

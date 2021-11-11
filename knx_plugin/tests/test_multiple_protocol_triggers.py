import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    def _build_appliances(self):
        sensore_movimento_a = home.appliance.sensor.motion.Appliance(
            "sensore di movimento a", []
        )
        sensore_movimento_b = home.appliance.sensor.motion.Appliance(
            "sensore di movimento b", []
        )
        luce = home.appliance.light.Appliance("una luce", [])
        collection = home.appliance.Collection()
        collection["luci"] = set([luce])
        collection["sensori"] = set([sensore_movimento_a, sensore_movimento_b])
        return collection

    def _build_performers(self):
        self.positive_triggers = list()
        self.negative_triggers = list()
        performers = list()
        appliance = self.appliances.find("una luce")
        knx_command = knx_plugin.command.dpt_switch.OnOff.make_from_yaml(
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
            [],
        )
        performers.append(luce_performer)
        for name, address in [
            ("sensore di movimento a", 0xCCCC),
            ("sensore di movimento b", 0xDDDD),
        ]:
            appliance = self.appliances.find(name)
            trigger_spotted = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
                [
                    address,
                ],
                [
                    home.event.motion.Event.Spotted,
                ],
            )
            trigger_missed = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
                [
                    address,
                ],
                [
                    home.event.motion.Event.Missed,
                ],
            )
            self.positive_triggers.append(trigger_spotted)
            self.negative_triggers.append(trigger_missed)
            performer = home.Performer(appliance.name, appliance, [], [trigger_spotted])
            performers.append(performer)
        return performers

    def _build_group_of_performers(self):
        return {
            "luci": [self._performers[0]],
            "sensori": [self._performers[1], self._performers[2]],
        }

    def _build_scheduler_triggers(self):
        t = home.scheduler.trigger.protocol.multi.Trigger(
            name="and",
            events=[home.appliance.light.event.forced.Event.On],
            positive_a=self.positive_triggers[0],
            negative_a=self.negative_triggers[0],
            positive_b=self.positive_triggers[1],
            negative_b=self.negative_triggers[1],
        )
        return [t]

    def _build_schedule_infos(self):
        return [
            (self.find_group_of_performers("luci"), self.find_scheduler_triggers("and"))
        ]


class TestLogics(TestCase):
    def test_multiple_protocol_trigger(tc):
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
                        home.appliance.light.event.forced.Event.On
                    )
                    i += 1

            async def emulate_bus_events(self):
                await asyncio.sleep(0.1)
                dpt = knx_stack.datapointtypes.DPT_Switch()
                dpt.action = "on"
                for address in [0xCCCC, 0xDDDD, 0xEEEE]:
                    address = knx_stack.GroupAddress(free_style=address)
                    tsap = tc.knx_gateway._association_table.get_tsap(address)
                    asaps = tc.knx_gateway._association_table.get_asaps(tsap)
                    for asap in asaps:
                        msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                            asap=asap, dpt=dpt
                        )
                        msg = tc._knx_gateway.protocol_instance.encode(msg)
                        tc._knx_gateway.protocol_instance.data_received(
                            msg.encode("utf-8")
                        )
                        await asyncio.sleep(0.1)

        test = Test("test_state")
        tc.assertFalse(
            tc.myhome.appliances.find("una luce").is_notified(
                home.appliance.light.event.forced.Event.On
            )
        )
        test.run()
        tc.assertTrue(
            tc.myhome.appliances.find("una luce").is_notified(
                home.appliance.light.event.forced.Event.On
            )
        )

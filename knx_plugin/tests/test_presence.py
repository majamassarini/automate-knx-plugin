import asyncio
import unittest

import home
import knx_plugin
import knx_stack
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    def _build_appliances(self):
        sensore_movimento = home.appliance.sensor.motion.Appliance(
            "sensore di movimento", []
        )
        luce = home.appliance.light.zone.Appliance("una luce", [])
        collection = home.appliance.Collection()
        collection["luci"] = set(
            [
                luce,
            ]
        )
        collection["sensori"] = set(
            [
                sensore_movimento,
            ]
        )
        return collection

    def _build_performers(self):
        performers = list()
        appliance = self.appliances.find("una luce")
        knx_command = knx_plugin.command.dpt_switch.OnOff.make_from_yaml(
            [
                0xBBBB,
            ]
        )
        knx_trigger_on = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
            [
                0xBBBB,
            ],
            [
                home.appliance.light.event.forced.Event.On,
            ],
        )
        knx_trigger_off = knx_plugin.trigger.dpt_switch.Off.make_from_yaml(
            [
                0xBBBB,
            ],
            [
                home.appliance.light.event.forced.Event.Off,
            ],
        )
        luce_performer = home.Performer(
            appliance.name,
            appliance,
            [
                knx_command,
            ],
            [knx_trigger_on, knx_trigger_off],
        )
        luce_performer.notify([home.event.sun.brightness.Event.DeepDark])
        performers.append(luce_performer)
        appliance = self.appliances.find("sensore di movimento")
        trigger_missed = knx_plugin.trigger.dpt_switch.Off.make_from_yaml(
            [
                0xEEEE,
            ],
            [
                home.event.motion.Event.Missed,
            ],
        )
        trigger_spotted = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
            [
                0xEEEE,
            ],
            [
                home.event.motion.Event.Spotted,
            ],
        )
        trigger_courtesy_on = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
            [
                0xEEEE,
            ],
            [
                home.event.presence.Event.On,
            ],
        )
        trigger_courtesy_off = knx_plugin.trigger.dpt_switch.Off.make_from_yaml(
            [
                0xEEEE,
            ],
            [
                home.event.presence.Event.Off,
            ],
        )
        sensore_performer = home.Performer(
            appliance.name,
            appliance,
            [],
            [
                trigger_missed,
                trigger_spotted,
                trigger_courtesy_on,
                trigger_courtesy_off,
            ],
        )
        performers.append(sensore_performer)
        return performers

    def _build_group_of_performers(self):
        return {"luci": [self._performers[0]], "sensori": [self._performers[1]]}

    def _build_scheduler_triggers(self):
        performers = self._group_of_performers["sensori"]
        triggers = list()
        for trigger in performers.triggers:
            t = home.scheduler.trigger.protocol.Trigger(
                name="presence", events=[], protocol_trigger=trigger
            )
            triggers.append(t)
        return triggers

    def _build_schedule_infos(self):
        return [
            (
                self.find_group_of_performers("luci"),
                self.find_scheduler_triggers("presence"),
            )
        ]


class TestLogics(TestCase):
    def test_presence(tc):
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
                        home.event.courtesy.Event.On
                    )
                    i += 1

            async def emulate_bus_events(self):
                await asyncio.sleep(0.1)
                dpt = knx_stack.datapointtypes.DPT_Switch()
                dpt.action = "on"
                tsap = tc.knx_gateway._association_table.get_tsap(
                    knx_stack.GroupAddress(free_style=0xEEEE)
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
        tc.assertFalse(
            tc.myhome.appliances.find("una luce").is_notified(
                home.event.presence.Event.On
            )
        )
        test.run()
        tc.assertTrue(
            tc.myhome.appliances.find("una luce").is_notified(
                home.event.presence.Event.On
            )
        )

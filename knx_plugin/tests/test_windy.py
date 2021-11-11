import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    def _build_appliances(self):
        anemometro = home.appliance.sensor.anemometer.Appliance("anemometro", [])
        tapparella = home.appliance.curtain.outdoor.Appliance("tapparella", [])
        collection = home.appliance.Collection()
        collection["tapparelle"] = set(
            [
                tapparella,
            ]
        )
        collection["sensori"] = set(
            [
                anemometro,
            ]
        )
        return collection

    def _build_performers(self):
        performers = list()
        appliance = self.appliances.find("anemometro")
        knx_trigger_windy = knx_plugin.trigger.dpt_value_wsp.Strong.make_from_yaml(
            [
                0xBBBB,
            ]
        )
        knx_trigger_quiet = knx_plugin.trigger.dpt_value_wsp.Weak.make_from_yaml(
            [
                0xBBBB,
            ]
        )
        performer = home.Performer(
            appliance.name, appliance, [], [knx_trigger_windy, knx_trigger_quiet]
        )
        performers.append(performer)
        appliance = self.appliances.find("tapparella")
        command = knx_plugin.command.dpt_updown.UpDown.make_from_yaml(
            [
                0xEEEE,
            ]
        )
        trigger_opened = knx_plugin.trigger.dpt_updown.Up.make_from_yaml(
            [
                0xEEEE,
            ],
            [home.appliance.curtain.event.forced.Event.Opened],
        )
        trigger_closed = knx_plugin.trigger.dpt_updown.Down.make_from_yaml(
            [
                0xEEEE,
            ],
            [home.appliance.curtain.event.forced.Event.Closed],
        )
        performer = home.Performer(
            appliance.name, appliance, [command], [trigger_opened, trigger_closed]
        )
        performer.notify(
            [
                home.event.sun.phase.Event.Sunset,
                home.event.sun.twilight.civil.Event.Sunset,
            ]
        )
        performers.append(performer)
        return performers

    def _build_group_of_performers(self):
        return {"tapparelle": [self._performers[1]], "sensori": [self._performers[0]]}

    def _build_scheduler_triggers(self):
        performers = self.find_group_of_performers("sensori")
        triggers = list()
        for t in performers.triggers:
            trigger = home.scheduler.trigger.protocol.Trigger(
                name="anemometro", events=[], protocol_trigger=t
            )
            triggers.append(trigger)
        return triggers

    def _build_schedule_infos(self):
        return [
            (
                self.find_group_of_performers("tapparelle"),
                self.find_scheduler_triggers("anemometro"),
            )
        ]


class TestLogics(TestCase):
    def test_windy(tc):
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
                    is_notified = tc.myhome.appliances.find("tapparella").is_notified(
                        home.event.wind.Event.Strong
                    )
                    i += 1

            async def emulate_bus_events(self):
                await asyncio.sleep(0.1)
                dpt = knx_stack.datapointtypes.DPT_Value_Wsp()
                dpt.encode(8.0)

                tsap = tc.knx_gateway._association_table.get_tsap(
                    knx_stack.GroupAddress(0xBBBB)
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
            tc.myhome.appliances.find("tapparella").is_notified(
                home.event.wind.Event.Strong
            )
        )
        test.run()
        tc.assertTrue(
            tc.myhome.appliances.find("tapparella").is_notified(
                home.event.wind.Event.Strong
            )
        )

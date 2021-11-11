import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    def _build_appliances(self):
        light = home.appliance.light.Appliance("a light", [])
        light.notify(home.event.sun.brightness.Event.DeepDark)
        another_light = home.appliance.light.Appliance("another light", [])
        another_light.notify(home.event.sun.brightness.Event.DeepDark)
        motion_sensor = home.appliance.sensor.motion.Appliance("motion sensor", [])
        collection = home.appliance.Collection()
        collection["lights"] = set([light, another_light])
        collection["sensors"] = set(
            [
                motion_sensor,
            ]
        )
        return collection

    def _build_performers(self):
        performers = list()
        appliance = self.appliances.find("a light")
        command = knx_plugin.command.dpt_switch.OnOff.make_from_yaml(
            [
                0xCCCC,
            ]
        )
        performer = home.Performer(appliance.name, appliance, [command], [])
        performers.append(performer)
        appliance = self.appliances.find("another light")
        command = knx_plugin.command.dpt_switch.OnOff.make_from_yaml(
            [
                0xDDDD,
            ]
        )
        performer = home.Performer(appliance.name, appliance, [command], [])
        performers.append(performer)
        appliance = self.appliances.find("motion sensor")
        trigger = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
            [
                0xBBBB,
            ],
            [home.event.courtesy.Event.On],
        )
        performer = home.Performer(appliance.name, appliance, [], [trigger])
        performers.append(performer)
        trigger = knx_plugin.trigger.dpt_switch.Off.make_from_yaml(
            [
                0xBBBB,
            ],
            [home.event.courtesy.Event.Off],
        )
        performer = home.Performer(appliance.name, appliance, [], [trigger])
        performers.append(performer)
        return performers

    def _build_group_of_performers(self):
        return {
            "lights": [self._performers[0], self._performers[1]],
            "motion spotted": [self._performers[2]],
            "motion missed": [self._performers[3]],
        }

    def _build_scheduler_triggers(self):
        triggers = list()
        for performer in self.find_group_of_performers("motion spotted"):
            for t in performer.triggers:
                trigger = home.scheduler.trigger.protocol.Trigger(
                    name="motion spotted trigger", events=[], protocol_trigger=t
                )
                triggers.append(trigger)
        for performer in self.find_group_of_performers("motion missed"):
            for t in performer.triggers:
                trigger = home.scheduler.trigger.protocol.delay.Trigger(
                    name="motion missed delay trigger",
                    events=[],
                    protocol_trigger=t,
                    timeout_seconds=1,
                )
                triggers.append(trigger)
        return triggers

    def _build_schedule_infos(self):
        return [
            (
                self.find_group_of_performers("lights"),
                self.find_scheduler_triggers("motion spotted trigger"),
            ),
            (
                self.find_group_of_performers("lights"),
                self.find_scheduler_triggers("motion missed delay trigger"),
            ),
        ]


class TestLogics(TestCase):
    async def emulate_bus_events(self):
        await asyncio.sleep(0.1)
        dpt_on = knx_stack.datapointtypes.DPT_Switch()
        dpt_on.action = "on"
        dpt_off = knx_stack.datapointtypes.DPT_Switch()
        dpt_off.action = "off"

        tsap = self.knx_gateway._association_table.get_tsap(
            knx_stack.GroupAddress(0xBBBB)
        )
        asaps = self.knx_gateway._association_table.get_asaps(tsap)
        for asap in asaps:
            msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                asap=asap, dpt=dpt_on
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)
            msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                asap=asap, dpt=dpt_off
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)
            msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                asap=asap, dpt=dpt_on
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)
            msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                asap=asap, dpt=dpt_off
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)
            msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                asap=asap, dpt=dpt_off
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)
            msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                asap=asap, dpt=dpt_on
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)

    @unittest.skip("to be improved")
    def testt_delay_trigger(self):
        self.enable_verbose_logging()

        myhome = Stub()
        self.make_process(myhome)
        self.add_knx_gateway(myhome, 2)
        asyncio.get_event_loop().create_task(self.emulate_bus_events())
        self.execute(myhome)

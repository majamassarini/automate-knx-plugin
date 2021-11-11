import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    def _build_appliances(self):
        scene = home.appliance.sensor.scene.Appliance("scene", [])
        light = home.appliance.light.Appliance("light", [])
        collection = home.appliance.Collection()
        collection["scene"] = set(
            [
                scene,
            ]
        )
        collection["light"] = set(
            [
                light,
            ]
        )
        return collection

    def _build_performers(self):
        performers = list()
        appliance = self.appliances.find("scene")
        knx_trigger_scene = (
            knx_plugin.trigger.dpt_scene_control.Activate.make_from_yaml(
                [
                    0xBBBB,
                ],
                [home.event.scene.Event.Triggered],
                number=16,
            )
        )
        performer = home.Performer(
            appliance.name,
            appliance,
            [],
            [
                knx_trigger_scene,
            ],
        )
        performers.append(performer)
        appliance = self.appliances.find("light")
        command = knx_plugin.command.dpt_switch.OnOff.make_from_yaml(
            [
                0xEEEE,
            ]
        )
        performer = home.Performer(appliance.name, appliance, [command], [])
        performers.append(performer)
        return performers

    def _build_group_of_performers(self):
        return {"scene": [self._performers[0]], "light": [self._performers[1]]}

    def _build_scheduler_triggers(self):
        performers = self.find_group_of_performers("scene")
        triggers = list()
        for t in performers.triggers:
            stop_timer_performers = list()
            stop_timer_performers.extend(self.find_group_of_performers("scene"))
            stop_timer_performers.extend(self.find_group_of_performers("light"))
            trigger = home.scheduler.trigger.protocol.timer.Trigger(
                name="scene",
                events=[home.appliance.light.event.forced.Event.On],
                protocol_trigger=t,
                timeout_seconds=0.01,
                stop_timer_events=[
                    home.event.scene.Event.Untriggered,
                ],
                stop_timer_performers=stop_timer_performers,
            )
            triggers.append(trigger)
        return triggers

    def _build_schedule_infos(self):
        return [
            (
                self.find_group_of_performers("light"),
                self.find_scheduler_triggers("scene"),
            )
        ]


class TestLogics(TestCase):
    async def emulate_bus_events(self):
        await asyncio.sleep(0.1)
        dpt = knx_stack.datapointtypes.DPTVimarScene()
        dpt.command = "attiva"
        dpt.index = 16

        tsap = self.knx_gateway._association_table.get_tsap(
            knx_stack.GroupAddress(0xBBBB)
        )
        asaps = self.knx_gateway._association_table.get_asaps(tsap)
        for asap in asaps:
            msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
                asap=asap, dpt=dpt
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)

    @unittest.skip("to be improved")
    def test_timer_trigger(self):
        self.enable_verbose_logging()

        myhome = Stub()
        self.make_process(myhome)
        self.add_knx_gateway(myhome, 1)

        self.assertTrue(
            myhome.appliances.find("scene").is_notified(
                home.event.scene.Event.Untriggered
            )
        )
        self.assertTrue(
            myhome.appliances.find("light").is_notified(
                home.appliance.light.event.forced.Event.Not
            )
        )
        asyncio.get_event_loop().create_task(self.emulate_bus_events())
        self.execute(myhome)
        self.assertTrue(
            myhome.appliances.find("scene").is_notified(
                home.event.scene.Event.Triggered
            )
        )
        self.assertTrue(
            myhome.appliances.find("light").is_notified(
                home.appliance.light.event.forced.Event.On
            )
        )

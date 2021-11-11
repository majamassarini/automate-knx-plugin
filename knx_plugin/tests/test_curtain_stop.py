import home
import asyncio
import unittest

import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    def _build_appliances(self):
        curtain = home.appliance.curtain.positionable.Curtain("curtain")
        rainmeter = home.appliance.sensor.rainmeter.Appliance("rainmeter")
        collection = home.appliance.Collection()
        collection["curtains"] = set(
            [
                curtain,
            ]
        )
        collection["sensors"] = set(
            [
                rainmeter,
            ]
        )
        return collection

    def _build_performers(self):
        performers = list()
        appliance = self.appliances.find("curtain")
        command_down = knx_plugin.command.dpt_updown.UpDown.make_from_yaml(
            [
                0xCCCC,
            ]
        )
        command_stop = knx_plugin.command.dpt_updown.Stop.make_from_yaml(
            [
                0xDDDD,
            ]
        )
        performer = home.Performer(
            appliance.name, appliance, [command_down, command_stop], []
        )
        performers.append(performer)
        appliance = self.appliances.find("rainmeter")
        trigger = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
            [
                0xBBBB,
            ],
            [
                home.event.rain.Event.Gentle,
            ],
        )
        performer = home.Performer(appliance.name, appliance, [], [trigger])
        performers.append(performer)
        return performers

    def _build_group_of_performers(self):
        return {"curtains": [self._performers[0]], "sensors": [self._performers[1]]}

    def _build_scheduler_triggers(self):
        triggers = list()
        stop_timer_performers = list()
        stop_timer_performers.extend(self.find_group_of_performers("curtains"))
        trigger = home.scheduler.trigger.state.timer.Trigger(
            name="stop curtain",
            events=[],
            state="Closing",
            timeout_seconds=0.2,
            stop_timer_events=[home.event.curtain.stop.Event.Stop],
            stop_timer_performers=stop_timer_performers,
        )
        triggers.append(trigger)
        for performer in self.find_group_of_performers("sensors"):
            for t in performer.triggers:
                trigger = home.scheduler.trigger.protocol.Trigger(
                    name="is raining", events=[], protocol_trigger=t
                )
                triggers.append(trigger)
        return triggers

    def _build_schedule_infos(self):
        return [
            (
                self.find_group_of_performers("curtains"),
                self.find_scheduler_triggers("is raining"),
            ),
            (
                self.find_group_of_performers("curtains"),
                self.find_scheduler_triggers("stop curtain"),
            ),
        ]


class TestLogics(TestCase):
    @unittest.skip("No more positionable.curtain modeled")
    def test_timer_trigger(self):
        self.enable_verbose_logging()
        description = {
            "type": "knx",
            "name": "DPT_Switch",
            "fields": {"action": "on"},
            "addresses": [0xBBBB],
        }
        command = knx_plugin.command.dpt_switch.OnOff(description)
        knx_curtain_engine = knx_plugin.bus.Emulator(
            [
                "0113130008000B01030000110096E00000CCCC010081",
                "0113130008000B01030000110096E00000DDDD010080",
            ]
        )  # request
        knx_curtain_engine.WAIT_FOR_MSGS = 2

        knx_curtain_engine.associate_commands([command])
        knx_curtain_engine.run([])
        msgs = command.execute()
        asyncio.get_event_loop().create_task(knx_curtain_engine.writer(msgs))

        myhome = Stub()

        self.assertFalse(
            myhome.appliances.find("curtain").is_notified(
                home.event.curtain.stop.Event.Stop
            )
        )

        self.make_process(myhome)
        self.add_knx_gateway(myhome)
        self.execute(myhome)
        knx_curtain_engine.disconnect()

        self.assertTrue(
            myhome.appliances.find("curtain").is_notified(
                home.event.curtain.stop.Event.Stop
            )
        )
        self.assertTrue(knx_curtain_engine.all_messages_received)

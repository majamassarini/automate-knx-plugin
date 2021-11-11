import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    class Switchhh(home.appliance.light.Appliance):
        def update_by(self, trigger, description):
            asyncio.get_event_loop().stop()
            return super(Stub.Switchhh, self).update_by(trigger, description)

    def _build_appliances(self):
        luce = Stub.Switchhh("una luce", [])
        collection = home.appliance.Collection()
        collection["luci"] = set(
            [
                luce,
            ]
        )
        return collection

    def _build_performers(self):
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
        return [luce_performer]

    def _build_group_of_performers(self):
        return {"luci": self._performers}

    def _build_scheduler_triggers(self):
        return []

    def _build_schedule_infos(self):
        return []


class TestLogics(TestCase):
    async def emulate_bus_events(self):
        await asyncio.sleep(0.1)
        dpt = knx_stack.datapointtypes.DPT_Switch()
        dpt.action = "on"

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
    def test_performer_update(self):
        self.enable_verbose_logging()

        myhome = Stub()
        self.make_process(myhome)
        self.add_knx_gateway(myhome, 10)

        self.assertFalse(
            myhome.appliances.find("una luce").is_notified(
                home.appliance.light.event.forced.Event.On
            )
        )
        asyncio.get_event_loop().create_task(self.emulate_bus_events())
        self.execute(myhome)
        self.assertTrue(
            myhome.appliances.find("una luce").is_notified(
                home.appliance.light.event.forced.Event.On
            )
        )

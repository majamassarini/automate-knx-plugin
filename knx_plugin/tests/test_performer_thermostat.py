import asyncio
import unittest

import home
import knx_stack
import knx_plugin
from knx_plugin.tests.testcase import TestCase


class Stub(home.MyHome):
    class Thermostatt(home.appliance.thermostat.presence.Appliance):
        def __init__(self, name, events):
            super(Stub.Thermostatt, self).__init__(name, events)
            self.was_forced_off = False
            self.was_forced_on = False
            self.was_forced_keep = False

        def update_by(self, trigger, description):
            t = super(Stub.Thermostatt, self).update_by(trigger, description)
            if "Forced Off" in self.state.compute():
                self.was_forced_off = True
            elif "Forced On" in self.state.compute():
                self.was_forced_on = True
            elif "Forced Keep" in self.state.compute():
                self.was_forced_keep = True
            return t

    def _build_appliances(self):
        termostato = Stub.Thermostatt("un termostato", [])
        termostato.notify(home.event.clima.season.Event.Summer)
        termostato.notify(home.event.clima.command.Event.Off)
        collection = home.appliance.Collection()
        collection["termostati"] = set(
            [
                termostato,
            ]
        )
        return collection

    def _build_performers(self):
        appliance = self.appliances.find("un termostato")
        command = knx_plugin.command.custom_clima.Setup.make_from_yaml([0xBBBB], 19, 20)
        trigger_on = knx_plugin.trigger.custom_clima.OnAutomatico.make_from_yaml(
            [0xBBBB], [], 19, 20
        )
        trigger_off = knx_plugin.trigger.custom_clima.Off.make_from_yaml(
            [0xBBBB], [], 19, 20
        )
        trigger_keep = knx_plugin.trigger.custom_clima.Keep.make_from_yaml(
            [0xBBBB], [], 19, 20
        )
        trigger_report = knx_plugin.trigger.custom_clima.Report.make_from_yaml(
            [0xBBBB], [], 19, 20
        )
        termostato_performer = home.Performer(
            appliance.name,
            appliance,
            [
                command,
            ],
            [trigger_on, trigger_off, trigger_keep, trigger_report],
        )
        return [termostato_performer]

    def _build_group_of_performers(self):
        return {"termostati": self._performers}

    def _build_scheduler_triggers(self):
        triggers = list()
        trigger = home.scheduler.trigger.interval.Trigger(
            name="force off", events=[], seconds=0.5
        )
        triggers.append(trigger)
        trigger = home.scheduler.trigger.interval.Trigger(
            name="force heat", events=[], seconds=0.6
        )
        triggers.append(trigger)
        trigger = home.scheduler.trigger.interval.Trigger(
            name="force keep", events=[], seconds=0.7
        )
        triggers.append(trigger)
        return triggers

    def _build_schedule_infos(self):
        return [
            (
                self.find_group_of_performers("termostati"),
                self.find_scheduler_triggers("force off"),
            ),
            (
                self.find_group_of_performers("termostati"),
                self.find_scheduler_triggers("force heat"),
            ),
            (
                self.find_group_of_performers("termostati"),
                self.find_scheduler_triggers("force keep"),
            ),
        ]


class TestLogics(TestCase):
    async def emulate_bus_events(self):
        await asyncio.sleep(0.1)
        dpt_off = knx_stack.datapointtypes.DPTSetupClima()
        dpt_off.funzionamento = "off"
        dpt_on = knx_stack.datapointtypes.DPTSetupClima()
        dpt_on.funzionamento = "automatico"
        dpt_keep = knx_stack.datapointtypes.DPTSetupClima()
        dpt_keep.funzionamento = "riduzione_notturna"

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
                asap=asap, dpt=dpt_keep
            )
            msg = self._knx_gateway.protocol_instance.encode(msg)
            self._knx_gateway.protocol_instance.data_received(msg.encode("utf-8"))
            await asyncio.sleep(0.1)

    @unittest.skip("to be improved")
    def test_performer_update(self):
        self.enable_verbose_logging()

        myhome = Stub()
        self.make_process(myhome)
        self.add_knx_gateway(myhome, 6)

        asyncio.get_event_loop().create_task(self.emulate_bus_events())
        self.execute(myhome)
        termostato = myhome.appliances.find("un termostato")
        self.assertTrue(termostato.was_forced_on)
        self.assertTrue(termostato.was_forced_off)
        self.assertTrue(termostato.was_forced_keep)

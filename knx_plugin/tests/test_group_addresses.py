# SPDX-License-Identifier: GPL-3.0-only
#
# automate home devices
#
# Copyright (C) 2021  Maja Massarini

import unittest

import knx_stack

import knx_plugin


class TestGroupAddressesOfBusDescriptions(unittest.TestCase):
    """
    A description received from the bus knows only its ASAP; the gateway
    fills in its group addresses, so the brain can tell which commands are
    for the device that sent it.
    """

    def setUp(self):
        self.gateway = knx_plugin.gateway.usbhid.Gateway(
            knx_plugin.client.usbhid.Client
        )
        self.trigger = knx_plugin.trigger.dpt_switch.On.make_from_yaml(
            [0x0C7A]
        )
        self.command = knx_plugin.command.dpt_switch.OnOff.make_from_yaml(
            [0x0C7A]
        )
        self.other_command = (
            knx_plugin.command.dpt_switch.OnOff.make_from_yaml([0x0C7B])
        )
        self.gateway.associate_triggers([self.trigger])
        self.gateway.associate_commands([self.command, self.other_command])

    def from_bus(self):
        msg = knx_stack.layer.application.a_group_value_write.ind.Msg(
            asap=self.trigger.asaps[0], dpt=self.trigger.dpt
        )
        return self.gateway._with_group_addresses(
            self.gateway.make_trigger(msg)
        )

    def test_a_bus_description_gets_its_group_addresses(self):
        description = self.from_bus()

        self.assertEqual(
            description.addresses, [knx_stack.GroupAddress(free_style=0x0C7A)]
        )

    def test_a_command_to_the_same_group_address_is_recognized(self):
        description = self.from_bus()

        self.assertTrue(self.command.reaches_a_device_of(description))
        self.assertFalse(self.other_command.reaches_a_device_of(description))

    def test_nothing_to_fill_in_for_an_unmanaged_message(self):
        self.assertIsNone(self.gateway._with_group_addresses(None))


if __name__ == "__main__":
    unittest.main()

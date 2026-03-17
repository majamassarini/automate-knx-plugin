# SPDX-License-Identifier: GPL-3.0-only
#
# automate home devices
#
# Copyright (C) 2021  Maja Massarini

import unittest
import unittest.mock
import asyncio
import knx_stack
from knx_plugin.client.knxnet_ip import Client


class TestDisconnectHandling(unittest.TestCase):

    @unittest.mock.patch('asyncio.get_running_loop')
    def test_manage_disconnect_request(self, mock_get_running_loop):
        """Test that client handles DISCONNECT_REQUEST from gateway"""
        mock_get_running_loop.return_value = unittest.mock.Mock()

        # Create a mock disconnect request
        disconnect_req = knx_stack.knxnet_ip.core.disconnect.req.Msg(
            addr_control_endpoint='192.168.1.1',
            port_control_endpoint=3671
        )

        # Create client instance with mocked parameters
        state = knx_stack.knxnet_ip.State(knx_stack.Medium.knxnet_ip, None, None)
        state.communication_channel_id = 5

        client = Client(
            on_con_close=unittest.mock.Mock(),
            knx_state=state,
            tasks=[],
            nat_local_addr='0.0.0.0',
            nat_local_port=0,
            local_addr='192.168.1.100',
            local_port=3671,
            remote_addr='192.168.1.1',
            remote_port=3671
        )

        # Mock transport
        client._transport = unittest.mock.Mock()

        # Call manage_disconnect_request
        client.manage_disconnect_request(disconnect_req)

        # Verify transport.sendto was called (sending DISCONNECT_RESPONSE)
        self.assertTrue(client._transport.sendto.called)

        # Verify transport.close was called
        self.assertTrue(client._transport.close.called)

    @unittest.mock.patch('asyncio.get_running_loop')
    def test_manage_server_tunneling_request_with_error(
        self, mock_get_running_loop
    ):
        """Test that client ACKs tunneling requests even with errors"""
        mock_get_running_loop.return_value = unittest.mock.Mock()

        # Create a tunneling request with E_SEQUENCE_NUMBER error
        tunneling_req = knx_stack.decode.knxnet_ip.tunneling.req.Msg(
            sequence_counter=5,
            status=knx_stack.knxnet_ip.ErrorCodes.E_SEQUENCE_NUMBER
        )

        # Create client instance
        state = knx_stack.knxnet_ip.State(knx_stack.Medium.knxnet_ip, None, None)
        state.communication_channel_id = 5

        client = Client(
            on_con_close=unittest.mock.Mock(),
            knx_state=state,
            tasks=[],
            nat_local_addr='0.0.0.0',
            nat_local_port=0,
            local_addr='192.168.1.100',
            local_port=3671,
            remote_addr='192.168.1.1',
            remote_port=3671
        )

        # Mock transport
        client._transport = unittest.mock.Mock()

        # Call manage_server_tunneling_request
        client.manage_server_tunneling_request(tunneling_req)

        # Verify ACK was sent (transport.sendto called)
        self.assertTrue(client._transport.sendto.called)

        # Verify reconnection was scheduled via the event loop
        self.assertTrue(
            mock_get_running_loop.return_value.create_task.called
        )

    @unittest.mock.patch('asyncio.get_running_loop')
    def test_manage_server_tunneling_request_success(
        self, mock_get_running_loop
    ):
        """Test that client handles successful tunneling requests"""
        mock_get_running_loop.return_value = unittest.mock.Mock()

        # Create a successful tunneling request
        tunneling_req = knx_stack.decode.knxnet_ip.tunneling.req.Msg(
            sequence_counter=5,
            status=knx_stack.knxnet_ip.ErrorCodes.E_NO_ERROR
        )

        # Create client instance
        state = knx_stack.knxnet_ip.State(knx_stack.Medium.knxnet_ip, None, None)
        state.communication_channel_id = 5

        client = Client(
            on_con_close=unittest.mock.Mock(),
            knx_state=state,
            tasks=[],
            nat_local_addr='0.0.0.0',
            nat_local_port=0,
            local_addr='192.168.1.100',
            local_port=3671,
            remote_addr='192.168.1.1',
            remote_port=3671
        )

        # Mock transport
        client._transport = unittest.mock.Mock()

        # Call manage_server_tunneling_request
        client.manage_server_tunneling_request(tunneling_req)

        # Verify ACK was sent
        self.assertTrue(client._transport.sendto.called)

        # Verify transport was NOT closed (successful request)
        self.assertFalse(client._transport.close.called)

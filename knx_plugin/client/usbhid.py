import asyncio
import logging

import knx_stack

from knx_plugin.client import Client as Parent


class MsgNotEncoded(Exception):
    """Knx msg has not been encoded"""


class Client(Parent):
    def data_received(self, data):
        msgs = self.decode(data)
        (reqs, cons, inds, others) = self.filter(msgs)
        for task in self._tasks:
            for msg in cons:
                self._loop.create_task(task(msg))
            for msg in inds:
                self._loop.create_task(task(msg))

    def decode(self, data):
        msgs = list()
        str_msgs = data.decode()
        splitted_data = str_msgs.split("\n")
        all_msgs = list()
        for msg in splitted_data:
            try:
                if msg:
                    octects_msg = knx_stack.Msg.make_from_str(msg)
                    self.logger.debug("received: {}".format(octects_msg))
                    msgs = knx_stack.decode_msg(self._state, octects_msg)
                    if msgs:
                        all_msgs.extend(msgs)
            except IndexError as e:
                self.logger.error(str(e) + " decoding msg: " + str(msg))
            except ValueError as e:
                self.logger.error(str(e) + " decoding msg: " + str(msg))
        return all_msgs

    def encode(self, msg):
        knx_msg = super(Client, self).encode(msg)
        self.logger.debug("sent: {}".format(knx_msg))
        knx_msg = str(knx_msg)
        padding = 112 - len(knx_msg)
        padded_msg = knx_msg + "0" * padding
        padded_msg += "\n"
        return padded_msg

    async def write(self, msgs, *args):
        await self._wait_for_transport()
        for msg in msgs:
            if isinstance(msg, knx_stack.layer.application.a_group_value_write.req.Msg):
                knx_msg = str(self.encode(msg))
                self.logger.info("written {}".format(knx_msg))
                self._transport.write(knx_msg.encode())


class ClientExample(object):
    def __init__(self):
        self._transport = None
        self._protocol = None

    def send_msg(self, msg, *args):
        state = args[0]
        new_state = state
        final_msg = None
        if isinstance(msg, knx_stack.layer.application.a_group_value_write.req.Msg):
            final_msg = knx_stack.encode_msg(state, msg)
        elif isinstance(msg, knx_stack.layer.application.a_group_value_read.req.Msg):
            final_msg = knx_stack.encode_msg(state, msg)
        if final_msg:
            self._transport.write(str(final_msg).encode())
        return new_state

    async def run(self):
        self._transport, self._protocol = await loop.create_connection(
            lambda: Client(None, []), "localhost", 5555
        )

        address_table = knx_stack.AddressTable(0x0000, [], 255)
        association_table = knx_stack.AssociationTable(address_table, {})

        new_association_table = association_table.associate(0x0E89, 1)
        from knx_stack.datapointtypes import DPT_Switch

        state = knx_stack.State(
            knx_stack.Medium.usb_hid, new_association_table, {1: DPT_Switch}
        )
        switch = DPT_Switch()
        switch.bits.action = DPT_Switch.Action.on
        req_msg = knx_stack.layer.application.a_group_value_write.req.Msg(
            asap=1, dpt=switch
        )

        while True:
            self.send_msg(req_msg, state)
            await asyncio.sleep(3)


if __name__ == "__main__":
    import sys

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    root.addHandler(handler)

    loop = asyncio.get_event_loop()
    loop.create_task(ClientExample().run())
    loop.run_forever()

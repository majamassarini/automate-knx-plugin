import knx_stack
from knx_plugin.gateway import Gateway as Parent


class Gateway(Parent):
    def __init__(self, client, host="0.0.0.0", port=5555):
        super(Gateway, self).__init__(client, host, port)

    def _init_state(self):
        self._knx_state = knx_stack.State(
            knx_stack.Medium.usb_hid, self._association_table, self._datapointtypes
        )

import copy

import home
from knx_plugin.message import Command as Parent


class Command(Parent):
    def __init__(self, description):
        super(Command, self).__init__(description)

    def _encode_winter_setpoint(self, setpoint):
        self.dpt.setpoint = int(setpoint * 10 - 50)

    def _encode_summer_setpoint(self, setpoint):
        self.dpt.setpoint = int(setpoint * 10 + 50)

    def _encode_setpoint(self, state):
        if home.event.clima.season.Event.Winter in state:
            self._encode_winter_setpoint(state.setpoint)
        else:
            self._encode_summer_setpoint(state.setpoint)

    def _encode_season(self, state):
        if home.event.clima.season.Event.Winter in state:
            self.dpt.stagione = "inverno"
        else:
            self.dpt.stagione = "estate"

    def _encode_funzionamento(self, state):
        if state.is_keeping:
            self.dpt.funzionamento = "riduzione_notturna"
        elif state.is_on:
            self.dpt.funzionamento = "automatico"
        else:
            self.dpt.funzionamento = "off"


class Setup(Command):
    """
    >>> import home
    >>> import knx_plugin
    >>> import knx_stack

    >>> cmd = knx_plugin.command.custom_clima.Setup.make([3202])
    >>> cmd._asaps = [1]
    >>> state = home.appliance.thermostat.presence.state.off.State()
    >>> first_state = home.appliance.thermostat.presence.state.off.State([0.0, home.event.clima.season.Event.Winter,
    ...                                                  home.event.clima.command.Event.Off,
    ...                                                  home.appliance.thermostat.presence.event.setpoint.Event(19),
    ...                                                  home.appliance.thermostat.presence.event.keep.setpoint.Event(19)])
    >>> msg = cmd.make_msgs_from(state, first_state)
    >>> knx_stack.Long(value=msg[0].dpt.value)
    0x10058C00
    >>> "off" in str(msg[0].dpt)
    True
    >>> "140" in str(msg[0].dpt)
    True
    >>> second_state = home.appliance.thermostat.presence.state.keep.State([0.0, home.event.clima.season.Event.Winter,
    ...                                                  home.event.clima.command.Event.Keep,
    ...                                                  home.appliance.thermostat.presence.event.setpoint.Event(20),
    ...                                                  home.appliance.thermostat.presence.event.keep.setpoint.Event(19)])
    >>> msg = cmd.make_msgs_from(first_state, second_state)
    >>> knx_stack.Long(value=msg[0].dpt.value)
    0x14058C00
    >>> "riduzione_notturna" in str(msg[0].dpt)
    True
    >>> "140" in str(msg[0].dpt)
    True
    >>> third_state = home.appliance.thermostat.presence.state.on.State([0.0, home.event.clima.season.Event.Winter,
    ...                                                  home.event.presence.Event.On,
    ...                                                  home.event.clima.command.Event.On,
    ...                                                  home.appliance.thermostat.presence.event.setpoint.Event(20),
    ...                                                  home.appliance.thermostat.presence.event.keep.setpoint.Event(19)])
    >>> msg = cmd.make_msgs_from(second_state, third_state)
    >>> knx_stack.Long(value=msg[0].dpt.value)
    0x18059600
    >>> "automatico" in str(msg[0].dpt)
    True
    >>> "150" in str(msg[0].dpt)
    True
    """

    DPT = {
        "name": "DPTSetupClima",
        "fields": {
            "funzionamento": "automatico",
            "centralizzato": True,  # invio dati dal termostato al sistema
            "stagione": "inverno",
            "terziario": False,  # anti bimbo
            "differenziale": 5,  # valori da 1 a 10 per esprimere valori da 0.1 a 1 grado centigrado
            "variazione_setpoint": 0,  # limite alla variazione del set point da parte dell'utente sul termostato
            "unita_misura": "celsius",
            "setpoint": 155,  # 20 gradi
            "temporizzazione": 0,
        },
        "addresses": [],
    }

    def make_msgs_from(self, old_state, new_state):
        result = []

        if (
            (old_state.season != new_state.season)
            or (old_state.mode != new_state.mode)
            or (old_state.setpoint != new_state.setpoint)
        ):
            self._encode_season(new_state)
            self._encode_setpoint(new_state)
            self._encode_funzionamento(new_state)

            result = self.execute()

        return result

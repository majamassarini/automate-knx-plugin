import copy

import home
import knx_stack

from knx_plugin.trigger import Always as Parent


class Trigger(Parent):
    def __init__(self, description, events, low_setpoint, high_setpoint):
        super(Trigger, self).__init__(description, events)
        self._low_setpoint = low_setpoint if low_setpoint else 20
        self._high_setpoint = high_setpoint if high_setpoint else 22

    @classmethod
    def make(cls, addresses, events=None, low_setpoint=None, high_setpoint=None):
        description = copy.deepcopy(cls.DPT)
        dsc = cls(description, events, low_setpoint, high_setpoint)
        dsc.addresses = addresses
        return dsc

    @classmethod
    def make_from_yaml(
        cls, addresses, events=None, low_setpoint=None, high_setpoint=None
    ):
        description = copy.deepcopy(cls.DPT)
        description["addresses"] = addresses
        return cls(description, events, low_setpoint, high_setpoint)

    @staticmethod
    def _decode_winter_setpoint(command):
        return (command.dpt.setpoint + 50) / 10

    @staticmethod
    def _decode_summer_setpoint(command):
        return (command.dpt.setpoint - 50) / 10

    def _decode_setpoint(self, command):
        if (
            command.dpt.stagione
            == knx_stack.datapointtypes.DPTSetupClima.Stagione.inverno
        ):
            setpoint = self._decode_winter_setpoint(command)
        else:
            setpoint = self._decode_summer_setpoint(command)

        return setpoint

    @staticmethod
    def _decode_season(command):
        if (
            command.dpt.stagione
            == knx_stack.datapointtypes.DPTSetupClima.Stagione.inverno
        ):
            season = home.event.clima.season.Event.Winter
        else:
            season = home.event.clima.season.Event.Summer
        return season

    @staticmethod
    def _decode_mode(command):
        if command.dpt.funzionamento in (
            knx_stack.datapointtypes.DPTSetupClima.Funzionamento.automatico,
            knx_stack.datapointtypes.DPTSetupClima.Funzionamento.manuale,
        ):
            mode = home.event.clima.command.Event.On
        elif (
            command.dpt.funzionamento
            == knx_stack.datapointtypes.DPTSetupClima.Funzionamento.riduzione_notturna
        ):
            mode = home.event.clima.command.Event.Keep
        elif (
            command.dpt.funzionamento
            == knx_stack.datapointtypes.DPTSetupClima.Funzionamento.off
        ):
            mode = home.event.clima.command.Event.Off
        else:
            mode = None
        return mode

    @staticmethod
    def _decode_temperatura(command):
        return command.dpt.temperatura + 15


class Force(Trigger):
    @property
    def forced_event(self):
        raise NotImplementedError

    @property
    def events(self):
        """
        Messages are sent continuously, not only when the user manually set the thermostat.
        Thus the thermostat should be made forced only if the sent message is different from
        the system state... make_new_state_from should be used instead of sending an event to the
        appliance every time the trigger is triggered
        """
        return []

    def make_new_state_from(self, another_description, old_state):
        mode = self._decode_mode(another_description)
        if mode not in old_state:
            new_state = old_state.next(self.forced_event)
        else:
            new_state = old_state
        return new_state


class Off(Force):

    DPT = {"name": "DPTSetupClima", "fields": {"funzionamento": "off"}, "addresses": []}

    @property
    def forced_event(self):
        return home.appliance.thermostat.presence.event.forced.Event.Off

    def is_triggered(self, another_description):
        if super(Off, self).is_triggered(another_description):
            return home.event.clima.command.Event.Off == self._decode_mode(
                another_description
            )
        else:
            return False


class Keep(Force):

    DPT = {
        "name": "DPTSetupClima",
        "fields": {"funzionamento": "riduzione_notturna"},
        "addresses": [],
    }

    @property
    def forced_event(self):
        return home.appliance.thermostat.presence.event.forced.Event.Keep

    def is_triggered(self, another_description):
        if super(Keep, self).is_triggered(another_description):
            return home.event.clima.command.Event.Keep == self._decode_mode(
                another_description
            )
        else:
            return False


class OnManuale(Force):

    DPT = {
        "name": "DPTSetupClima",
        "fields": {"funzionamento": "manuale", "stagione": "inverno"},
        "addresses": [],
    }

    @property
    def forced_event(self):
        return home.appliance.thermostat.presence.event.forced.Event.On

    def is_triggered(self, another_description):
        if super(OnManuale, self).is_triggered(another_description):
            return home.event.clima.command.Event.On == self._decode_mode(
                another_description
            )
        else:
            return False


class OnAutomatico(Force):

    DPT = {
        "name": "DPTSetupClima",
        "fields": {"funzionamento": "automatico", "stagione": "inverno"},
        "addresses": [],
    }

    @property
    def forced_event(self):
        return home.appliance.thermostat.presence.event.forced.Event.On

    def is_triggered(self, another_description):
        if super(OnAutomatico, self).is_triggered(another_description):
            return home.event.clima.command.Event.On == self._decode_mode(
                another_description
            )
        else:
            return False


class Report(Trigger):
    """
    >>> import home
    >>> import knx_plugin
    >>> import copy
    >>> cmd = knx_plugin.trigger.custom_clima.Report.make_from_yaml([3202], [], 19, 20)
    >>> cmd._asaps = [1]
    >>> cmd.dpt.value = 0x00E3E369
    >>> description = copy.copy(knx_plugin.trigger.custom_clima.Report.DPT)
    >>> description["addresses"] = [3202]
    >>> description["fields"]["funzionamento"] = "off"
    >>> another_cmd = knx_plugin.trigger.custom_clima.Off(description, [], 12, 12)
    >>> cmd.make_new_state_from(another_cmd,
    ...                         home.appliance.thermostat.presence.state.off.State([0.0,
    ...                                                                       home.event.clima.season.Event.Winter,
    ...                                                                       home.event.clima.command.Event.On]))
    Off (computed from events: 43.0, Setpoint: 22.5°, Keeping mode setpoint: 21.5°, home.event.clima.season.Event.Winter, home.event.clima.command.Event.Off, home.event.presence.Event.Off, home.appliance.thermostat.presence.event.forced.event.Event.Not) and disabled events set()
    """

    DPT = {
        "name": "DPTInfoClimaReport",
        "fields": {
            "funzionamento": "automatico_invio_temperatura_abilitato",
            "centralizzato": True,
            "stagione": "inverno",
            "terziario": True,
            "stato_rele": False,
            "setpoint": 150,  # 20 gradi
            "temporizzazione": 0,
            "temperatura": 28,
        },
        "addresses": [],
    }

    def make_new_state_from(self, another_description, old_state):
        setpoint = self._decode_setpoint(another_description)
        temperature = self._decode_temperatura(another_description)
        season = self._decode_season(another_description)
        mode = self._decode_mode(another_description)

        new_state = old_state.next(season)
        new_state = new_state.next(mode)
        new_state = new_state.next(temperature)
        # new_state.setpoint = setpoint  # change it just through the web ui or scheduled jobs

        return new_state

from knx_plugin.trigger import Always as Parent


class Always(Parent):

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Power",
        "addresses": [],
        "fields": {"decoded_value": 0},
    }


from knx_plugin.trigger.dpt_value_power import consumption
from knx_plugin.trigger.dpt_value_power import production

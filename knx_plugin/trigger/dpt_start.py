from knx_plugin.trigger import Equal


class Start(Equal):

    DPT = {
        "type": "knx",
        "name": "DPT_Start",
        "addresses": [],
        "fields": {"action": "start"},
    }


class Stop(Equal):

    DPT = {
        "type": "knx",
        "name": "DPT_Start",
        "addresses": [],
        "fields": {"action": "stop"},
    }

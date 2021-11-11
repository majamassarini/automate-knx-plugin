from knx_plugin.trigger import Equal


class On(Equal):

    DPT = {
        "type": "knx",
        "name": "DPT_Switch",
        "addresses": [],
        "fields": {"action": "on"},
    }


class Off(Equal):

    DPT = {
        "type": "knx",
        "name": "DPT_Switch",
        "addresses": [],
        "fields": {"action": "off"},
    }

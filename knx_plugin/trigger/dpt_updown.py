from knx_plugin.trigger import Equal


class Up(Equal):

    DPT = {
        "type": "knx",
        "name": "DPT_UpDown",
        "addresses": [],
        "fields": {"direction": "up"},
    }


class Down(Equal):

    DPT = {
        "type": "knx",
        "name": "DPT_UpDown",
        "addresses": [],
        "fields": {"direction": "down"},
    }

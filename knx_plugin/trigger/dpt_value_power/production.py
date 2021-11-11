import home

from knx_plugin.trigger import GreaterThan


class No(GreaterThan):
    """
    >>> import io
    >>> import json
    >>> import knx_stack
    >>> import knx_plugin

    >>> addresses = [knx_stack.GroupAddress(free_style=1234),]
    >>> producing = knx_plugin.trigger.dpt_value_power.production.No.make(addresses=addresses)

    >>> address_table = knx_stack.layer.AddressTable(knx_stack.Address(4098), [], 255)
    >>> association_table = knx_stack.layer.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()
    >>> producing.associate(association_table, groupobject_table)

    >>> bus_event = '''
    ...        {"name": "DPT_Value_Power",
    ...         "addresses": [1234],
    ...         "fields": {"decoded_value": 600}}
    ... '''
    >>> another_description = knx_plugin.Description(json.loads(bus_event))
    >>> another_description.associate_with(association_table)
    >>> producing.is_triggered(another_description)
    True
    """

    DPT = {
        "type": "knx",
        "name": "DPT_Value_Power",
        "addresses": [],
        "fields": {"decoded_value": 0},
    }

    DEFAULT_EVENTS = [home.event.power.production.Event.No]

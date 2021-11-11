.. knx-plugin documentation master file, created by
   sphinx-quickstart on Wed Jan 27 10:59:40 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

automate-knx-plugin documentation
========================

**knx-plugin** is a library which translates **Appliance's state changes** into *KNX commands* and
**KNX events** into *messages for Appliances*.

An **Appliance** is a non deterministic state machine, abstract representation of one or more physical devices.

Examples
========

KNX events
----------

When the button is pressed the *Light Appliance* is **Forced On**.

.. doctest:: knx_event

    >>> import json
    >>> import home
    >>> import knx_stack
    >>> import knx_plugin

    >>> # Setup the KNX stack
    >>> address_table = knx_stack.AddressTable(knx_stack.Address(4097), [], 255)
    >>> association_table = knx_stack.AssociationTable(address_table, [])
    >>> groupobject_table = knx_stack.GroupObjectTable()

    >>> # Build a Trigger which triggers the message sent by the button when it is pressed
    >>> trigger = knx_plugin.trigger.dpt_switch.On.make(addresses=[knx_stack.GroupAddress(free_style=1234),],
    ...                                                 events=[home.appliance.light.event.forced.Event.On])
    >>> trigger.associate(association_table, groupobject_table)

    >>> # Simulate reception of a message sent by the button when Off is pressed and the trigger is not triggered
    >>> dpt = knx_stack.datapointtypes.DPT_Switch()
    >>> dpt.bits.action = dpt.Action.off
    >>> asap = association_table.get_asaps_from_address(knx_stack.GroupAddress(free_style=1234))[0]
    >>> bus_event = knx_stack.layer.application.a_group_value_write.ind.Msg(asap, dpt)
    >>> event = knx_plugin.Description.make_from(bus_event)
    >>> trigger.is_triggered(event)
    False

    >>> # Simulate reception of a message sent by the button when On is pressed and the trigger is triggered
    >>> dpt.bits.action = dpt.Action.on
    >>> event = knx_plugin.Description.make_from(bus_event)
    >>> trigger.is_triggered(event)
    True

    >>> # Since the trigger has been triggered the Light Appliance can be notified with the trigger's event
    >>> appliance = home.appliance.light.presence.Appliance("a light", [])
    >>> old_state, new_state = appliance.notify(trigger.events[0])
    >>> old_state
    Off (computed from events: home.event.presence.Event.Off, home.appliance.light.event.forced.event.Event.Not) and disabled events set()
    >>> new_state
    Forced On (computed from events: home.event.presence.Event.Off, home.appliance.light.event.forced.event.Event.On) and disabled events set()


Adjust *Lux Sensor Appliance* **brightness** when receiving lux messages from lux sensor device

.. doctest:: knx_event

    >>> import home
    >>> import knx_plugin

    >>> # Create a trigger which triggers any lux value
    >>> trigger = knx_plugin.trigger.dpt_value_lux.Always.make([1234])

    >>> # Simulate reception of a new lux value from bus
    >>> bus_event = '''
    ...     {"name": "DPT_Value_Lux",
    ...      "addresses": [1234],
    ...      "fields": {"decoded_value": 1.0}}
    ... '''
    >>> description = (knx_plugin.Description(json.loads(bus_event)))

    >>> # Update the Lux Sensor Appliance using data in the knx message
    >>> appliance = home.appliance.sensor.luxmeter.Appliance("a lux sensor", [0.0])
    >>> appliance.state
    0.0 lux (computed from events: 0.0) and disabled events set()
    >>> trigger.make_new_state_from(description, appliance.state)
    1.0 lux (computed from events: 1.0) and disabled events set()


.. toctree::
   :maxdepth: 5

   messages
   clients
   gateways

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

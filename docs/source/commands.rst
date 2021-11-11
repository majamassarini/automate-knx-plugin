Commands
********

Commands are entities **capable of forge** messages for the KNX bus interpreting changes in *Appliance* state.

Commands *compare* an *old Appliance state* with a *new one* and create messages to be sent to the Appliance's device.

Commands are designed to read *Appliance's attributes*: :meth:`home.appliance.attribute.mixin`

.. autoclass:: knx_plugin.message.Command

.. toctree::
   :maxdepth: 4

   command/dpt_switch
   command/dpt_updown


DPT_Brightness
--------------

.. autoclass:: knx_plugin.command.dpt_brightness.Brightness

Custom Clima
------------

.. autoclass:: knx_plugin.command.custom_clima.Setup

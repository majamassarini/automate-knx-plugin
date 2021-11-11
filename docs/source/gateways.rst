Gateway
=======

It is the **home instance** gateway to the **Knx bus**.
Connects triggers and commands to the **KNX bus**.
It depends on the physical connecting device, it could be both a USB HID device or a KNXNET IP device.

Abstract
--------

.. autoclass:: knx_plugin.gateway.Gateway

USB HID
^^^^^^^

.. autoclass:: knx_plugin.gateway.usbhid.Gateway

KNXNET IP
^^^^^^^^^

.. autoclass:: knx_plugin.gateway.knxnet_ip.Gateway
   :no-members:


Clients
=======

A client is used by a :meth:`knx_plugin.gateway.definition.Gateway` to connect the **KNX bus** through a *KNX gateway device*.

Abstract
--------

.. autoclass:: knx_plugin.client.Client

USB HID
-------

The connected *knx gateway device* is a **USB HID device**.

.. autoclass:: knx_plugin.client.usbhid.Client
   :no-members:

KNXNET IP
---------

The connected *knx gateway device* is a **KNXNET IP device**.

.. autoclass:: knx_plugin.client.knxnet_ip.Client
   :no-members:

# automate-knx-plugin
[![Build Status](https://app.travis-ci.com/majamassarini/automate-knx-plugin.svg?branch=main)](https://app.travis-ci.com/majamassarini/automate-knx-plugin)
[![codecov](https://codecov.io/gh/majamassarini/automate-knx-plugin/branch/main/graph/badge.svg?token=1W74jfuBfb)](https://codecov.io/gh/majamassarini/automate-knx-plugin)
[![Documentation Status](https://readthedocs.org/projects/automate-knx-plugin/badge/?version=latest)](https://automate-knx-plugin.readthedocs.io/en/latest/?badge=latest)

The **KNX** plugin for the [automate-home project](https://github.com/majamassarini/automate-home).

## Yaml examples of usage

Trigger and command for a simple [presence light model](https://automate-home.readthedocs.io/en/latest/appliances.html#light-presence-appliance).
```yaml
- !Performer
  name: "trigger forced on/off"
  for appliance: "an indoor presence light"
  commands: [ ]
  triggers:
    - !knx_plugin.trigger.dpt_switch.On
      addresses: [ 0x0DE1, 0x0F41 ]
      events:
        - !home.appliance.light.event.forced.Event.On
    - !knx_plugin.trigger.dpt_switch.Off
      addresses: [ 0x0DE1, 0x0F41 ]
      events:
        - !home.appliance.light.event.forced.Event.Off

- !Performer
  name: "command on/off"
  for appliance: "an indoor presence light"
  commands:
    - !knx_plugin.command.dpt_switch.OnOff { addresses: [ 0x0DE1, 0x0F41 ] }
  triggers: [ ]
```

Trigger and command for a more complex [indoor dimmerable light model](https://automate-home.readthedocs.io/en/latest/appliances.html#light-indoor-dimmerable-appliance).
```yaml
- !Performer
  name: "trigger forced on/circadian rhythm/lux balancing/off"
  for appliance: "an indoor dimmerable light"
  commands: []
  triggers:
    - !knx_plugin.trigger.dpt_switch.On # forced on from on/off button 1 & 2
      addresses: [ 0x0F41, 0xF45, ]
      events:
        - !home.appliance.light.indoor.dimmerable.event.forced.Event.CircadianRhythm
    - !knx_plugin.trigger.dpt_switch.On # forced on from on/off button 3
      addresses: [ 0x0DD1, ]
      events:
        - !home.appliance.light.indoor.dimmerable.event.forced.Event.LuxBalance
    - !knx_plugin.trigger.dpt_scene_control.Activate # forced on from a scene button
      addresses: [ 0x0B07 ]
      number: 7
      events:
        - !home.appliance.light.indoor.dimmerable.event.forced.Event.On
    - !knx_plugin.trigger.dpt_switch.Off # forced off from button 1 or 2
      addresses: [ 0x0F41, 0x0F45, 0x0DD1, ]
      events:
        - !home.appliance.light.indoor.dimmerable.event.forced.Event.Off

- !Performer
  name: "command on/off and brightness"
  for appliance: "an indoor dimmerable light"
  commands:
    - !knx_plugin.command.dpt_switch.OnOff { addresses: [ 0x0DD1, ] }
    - !knx_plugin.command.dpt_brightness.Brightness { addresses: [ 0x0DD2, ] }
  triggers: [ ]
```


## Documentation

* [automate-home protocol commands/triggers chapter](https://automate-home.readthedocs.io/en/latest/performer.html)
* [automate-knx-plugin documentation](https://automate-knx-plugin.readthedocs.io/en/latest/?badge=latest)

## Contributing

Pull requests are welcome!

## License

The automate-knx-plugin is licensed under MIT.
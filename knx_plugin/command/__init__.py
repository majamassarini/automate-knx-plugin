from typing import TypeVar, Type

import home

OnOffAppliance = TypeVar(
    "OnOffAppliance",
    Type[home.appliance.light.state.State],
    Type[home.appliance.socket.presence.state.State],
    Type[home.appliance.socket.energy_guard.state.State],
    Type[home.appliance.sound.player.state.State],
    Type[home.appliance.sprinkler.state.State],
)

OpenCloseAppliance = TypeVar(
    "OpenCloseAppliance",
    Type[home.appliance.curtain.indoor.blackout.state.State],
    Type[home.appliance.curtain.outdoor.state.State],
)


from knx_plugin.command import custom_clima, dpt_brightness, dpt_switch, dpt_updown

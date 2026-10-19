"""The Hargassner HSV integration.

Reads a Hargassner HSV 22 pellet boiler, an ESR21 solar controller and the
house electricity meter from the data logger on a Raspberry Pi. Strictly
read-only: the boiler only transmits, there is no way back to it.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HargassnerApi, HargassnerApiError, HargassnerAuthError
from .const import API_MAJOR, DOMAIN, STATE_INTERVAL, TOTALS_INTERVAL
from .coordinator import HargassnerCoordinator, HargassnerRuntime
from .entity import device_info

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

type HargassnerConfigEntry = ConfigEntry[HargassnerRuntime]


def api_supported(info: dict) -> bool:
    """True if the Pi speaks a contract version this integration understands."""
    return str(info.get("api_version", "")).split(".")[0] == str(API_MAJOR)


async def async_setup_entry(hass: HomeAssistant, entry: HargassnerConfigEntry) -> bool:
    """Set up Hargassner HSV from a config entry."""
    api = HargassnerApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_TOKEN],
    )
    try:
        info = await api.info()
    except HargassnerAuthError as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN, translation_key="invalid_auth"
        ) from err
    except HargassnerApiError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="cannot_connect"
        ) from err
    if not api_supported(info):
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="unsupported_api",
            translation_placeholders={"version": str(info.get("api_version"))},
        )

    state = HargassnerCoordinator(hass, entry, "state", api.state, STATE_INTERVAL)
    totals = HargassnerCoordinator(hass, entry, "totals", api.totals, TOTALS_INTERVAL)
    await state.async_config_entry_first_refresh()
    await totals.async_config_entry_first_refresh()

    # The Pi is the hub; register it first so the other devices can link to it.
    hub = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, **device_info(info, "logger")
    )
    entry.runtime_data = HargassnerRuntime(
        api=api, info=info, state=state, totals=totals, hub_device_id=hub.id
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HargassnerConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: HargassnerConfigEntry) -> None:
    """Reload after the options (selected sources) changed."""
    await hass.config_entries.async_reload(entry.entry_id)

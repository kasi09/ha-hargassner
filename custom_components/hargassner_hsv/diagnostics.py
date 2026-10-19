"""Diagnostics for the Hargassner HSV integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant

from . import HargassnerConfigEntry

TO_REDACT = {CONF_TOKEN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HargassnerConfigEntry
) -> dict[str, Any]:
    runtime = entry.runtime_data
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "info": runtime.info,
        "state": runtime.state.data,
        "totals": runtime.totals.data,
    }

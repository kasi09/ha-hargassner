"""Diagnostics must never contain the token."""

import json

from homeassistant.core import HomeAssistant

from custom_components.hargassner_hsv.diagnostics import async_get_config_entry_diagnostics

from .conftest import TOKEN


async def test_token_redacted(hass: HomeAssistant, mock_pi, config_entry) -> None:
    mock_pi()
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    diag = await async_get_config_entry_diagnostics(hass, config_entry)
    assert TOKEN not in json.dumps(diag)
    assert diag["entry"]["data"]["token"] == "**REDACTED**"
    assert diag["state"]["boiler"]["state"]

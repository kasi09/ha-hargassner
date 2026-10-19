"""Setup, entities, availability and statistics classes."""

import copy

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import BASE, load


async def setup(hass, config_entry):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


def eid(hass, key: str, domain: str = "sensor") -> str:
    reg = er.async_get(hass)
    entity_id = reg.async_get_entity_id(domain, "hargassner_hsv", f"00000000-0000-4000-8000-000000000001_{key}")
    assert entity_id, key
    return entity_id


async def test_setup_and_values(hass: HomeAssistant, mock_pi, config_entry) -> None:
    mock_pi()
    await setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    state = load("state")

    s = hass.states.get(eid(hass, "boiler_state"))
    assert s.state == state["boiler"]["state"]
    assert "full_load" in s.attributes["options"]

    s = hass.states.get(eid(hass, "solar_heat_power"))
    assert float(s.state) == state["solar"]["power_kw"]
    assert s.attributes["origin"] == "calculated"
    assert s.attributes["flow_assumption_l_h"] == 48.0

    s = hass.states.get(eid(hass, "solar_heat_total"))
    assert s.attributes["state_class"] == "total_increasing"

    # calculated grand totals must NOT be total_increasing: a corrected assumption
    # lowers them, and HA would count the drop as a meter reset
    s = hass.states.get(eid(hass, "boiler_heat_total"))
    assert s.attributes["state_class"] == "total"

    # daily values carry last_reset at midnight
    s = hass.states.get(eid(hass, "solar_heat_today"))
    assert s.attributes["state_class"] == "total"
    assert s.attributes["last_reset"].startswith(load("totals")["today_start"][:10])

    s = hass.states.get(eid(hass, "solar_pump", "binary_sensor"))
    assert s.state == ("on" if state["solar"]["pump_on"] else "off")


async def test_disabled_by_default(hass, mock_pi, config_entry) -> None:
    mock_pi()
    await setup(hass, config_entry)
    reg = er.async_get(hass)
    for key in ("solar_meter_raw", "solar_flow", "counter_a", "o2_target"):
        assert reg.async_get(eid(hass, key)).disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_stale_source_unavailable(hass, mock_pi, config_entry) -> None:
    state = copy.deepcopy(load("state"))
    state["sources"]["solar"]["fresh"] = False
    state["solar"] = {k: None for k in state["solar"]}
    mock_pi(state=state)
    await setup(hass, config_entry)
    assert hass.states.get(eid(hass, "collector_temp")).state == STATE_UNAVAILABLE
    # other sources stay available
    assert hass.states.get(eid(hass, "boiler_temp")).state != STATE_UNAVAILABLE


async def test_only_heat_devices(hass, mock_pi, config_entry) -> None:
    """Meter, sub-meter and weather are read directly by HA, not via this integration."""
    mock_pi()
    await setup(hass, config_entry)
    reg = er.async_get(hass)
    for key in ("grid_import_power", "dairy_power", "weather_temperature", "base_load"):
        assert reg.async_get_entity_id(
            "sensor", "hargassner_hsv", f"00000000-0000-4000-8000-000000000001_{key}"
        ) is None


async def test_auth_failure_starts_reauth(hass, aioclient_mock, config_entry) -> None:
    aioclient_mock.get(f"{BASE}/info", status=401)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == "reauth" for f in flows)


async def test_pi_offline_retries(hass, aioclient_mock, config_entry) -> None:
    aioclient_mock.get(f"{BASE}/info", exc=TimeoutError)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unsupported_api(hass, aioclient_mock, config_entry) -> None:
    aioclient_mock.get(f"{BASE}/info", json={**load("info"), "api_version": "2.0"})
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_unload(hass, mock_pi, config_entry) -> None:
    mock_pi()
    await setup(hass, config_entry)
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_devices_linked_to_hub(hass, mock_pi, config_entry) -> None:
    from homeassistant.helpers import device_registry as dr

    mock_pi()
    await setup(hass, config_entry)
    reg = dr.async_get(hass)
    iid = "00000000-0000-4000-8000-000000000001"
    devices = {
        ident[1]: d
        for d in dr.async_entries_for_config_entry(reg, config_entry.entry_id)
        for ident in d.identifiers
    }
    hub, boiler = devices.get(f"{iid}_logger"), devices.get(f"{iid}_boiler")
    assert len(devices) == 3
    assert hub and boiler
    assert boiler.via_device_id == hub.id
    assert boiler.sw_version == "282182h / SMS V4.3h"

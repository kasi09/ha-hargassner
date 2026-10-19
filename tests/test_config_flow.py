"""Config flow tests."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.hargassner_hsv.const import DOMAIN

from .conftest import BASE, INSTALLATION_ID, load


async def test_user_flow_success(hass: HomeAssistant, aioclient_mock, entry_data) -> None:
    aioclient_mock.get(f"{BASE}/info", json=load("info"))
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    with patch("custom_components.hargassner_hsv.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hargassner HSV 22"
    assert result["result"].unique_id == INSTALLATION_ID
    # the token is sent as bearer header
    assert aioclient_mock.mock_calls[-1][3]["Authorization"] == "Bearer test-token-nicht-echt"


async def test_user_flow_errors(hass: HomeAssistant, aioclient_mock, entry_data) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    aioclient_mock.get(f"{BASE}/info", status=401)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "invalid_auth"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/info", exc=TimeoutError)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/info", json={**load("info"), "api_version": "2.0"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "unsupported_api"}


async def test_already_configured(hass, aioclient_mock, config_entry, entry_data) -> None:
    config_entry.add_to_hass(hass)
    aioclient_mock.get("http://neu.example:8080/api/ha/v1/info", json=load("info"))
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**entry_data, CONF_HOST: "neu.example"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data[CONF_HOST] == "neu.example"      # address updated


async def test_reauth(hass, mock_pi, config_entry) -> None:
    mock_pi()
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TOKEN: "neuer-token"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_TOKEN] == "neuer-token"
    assert config_entry.data[CONF_PORT] == 8080
    await hass.async_block_till_done()

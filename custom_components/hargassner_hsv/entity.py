"""Base entity for the Hargassner HSV integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HargassnerCoordinator, HargassnerRuntime

DEVICE_MODEL: dict[str, tuple[str | None, str]] = {
    "boiler": ("Hargassner", "HSV 22"),
    "solar": ("Technische Alternative", "ESR21"),
    "logger": ("Raspberry Pi", "hsv-web data logger"),
}


def device_info(
    info: dict[str, Any], device: str, hub_device_id: str | None = None
) -> DeviceInfo:
    """One HA device per source; the Pi (logger) is the hub.

    The hub is linked by its registry id (via_device_id). The older
    identifier tuple (via_device) stops working in HA 2027.8.
    """
    iid = info["installation_id"]
    manufacturer, model = DEVICE_MODEL[device]
    if device == "boiler":
        manufacturer, model = info.get("manufacturer", manufacturer), info.get("model", model)
    result = DeviceInfo(
        identifiers={(DOMAIN, f"{iid}_{device}")},
        translation_key=device,
        manufacturer=manufacturer,
        model=model,
    )
    if device == "boiler":
        fw = info.get("firmware") or {}
        result["sw_version"] = " / ".join(v for v in (fw.get("eprom"), fw.get("display")) if v)
    if device == "logger":
        result["sw_version"] = info.get("software")
    elif hub_device_id:
        result["via_device_id"] = hub_device_id
    return result


@dataclass(frozen=True, kw_only=True)
class HargassnerEntityDescription(EntityDescription):
    """Where a value lives and to which device it belongs."""

    device: str
    # Key in state["sources"]; the entity is unavailable while it is stale.
    source: str | None = None
    coordinator: str = "state"


class HargassnerEntity(CoordinatorEntity[HargassnerCoordinator]):
    """Common behaviour: unique id, device, availability by data age."""

    _attr_has_entity_name = True
    entity_description: HargassnerEntityDescription

    def __init__(
        self, runtime: HargassnerRuntime, description: HargassnerEntityDescription
    ) -> None:
        coordinator = runtime.totals if description.coordinator == "totals" else runtime.state
        super().__init__(coordinator)
        self.entity_description = description
        self.runtime = runtime
        self._attr_unique_id = f"{runtime.info['installation_id']}_{description.key}"
        self._attr_device_info = device_info(
            runtime.info, description.device, runtime.hub_device_id
        )

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        source = self.entity_description.source
        if source is None:
            return True
        meta = (self.coordinator.data.get("sources") or {}).get(source) or {}
        return bool(meta.get("fresh"))

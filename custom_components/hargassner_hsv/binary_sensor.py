"""Binary sensors for the Hargassner HSV integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HargassnerConfigEntry
from .const import CONF_SOURCES, SOURCES
from .entity import HargassnerEntity, HargassnerEntityDescription

SERVICES = ("hsv-logger", "hsv-solar", "hsv-strom", "hsv-web", "hsv-waechter")


@dataclass(frozen=True, kw_only=True)
class HargassnerBinaryDescription(
    HargassnerEntityDescription, BinarySensorEntityDescription
):
    value_fn: Callable[[dict[str, Any]], bool | None]


def _service(name: str) -> Callable[[dict[str, Any]], bool | None]:
    def value(data: dict[str, Any]) -> bool | None:
        state = ((data.get("system") or {}).get("services") or {}).get(name)
        return None if state is None else state == "active"
    return value


DESCRIPTIONS: tuple[HargassnerBinaryDescription, ...] = (
    HargassnerBinaryDescription(
        key="solar_pump",
        translation_key="solar_pump",
        device="solar",
        source="solar",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: (d.get("solar") or {}).get("pump_on"),
    ),
    *(
        HargassnerBinaryDescription(
            key=f"service_{name.replace('-', '_')}",
            translation_key=f"service_{name.replace('-', '_')}",
            device="logger",
            coordinator="totals",
            device_class=BinarySensorDeviceClass.RUNNING,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=_service(name),
        )
        for name in SERVICES
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HargassnerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    selected = entry.options.get(CONF_SOURCES, list(SOURCES))
    runtime = entry.runtime_data
    async_add_entities(
        HargassnerBinarySensor(runtime, d) for d in DESCRIPTIONS if d.device in selected
    )


class HargassnerBinarySensor(HargassnerEntity, BinarySensorEntity):
    entity_description: HargassnerBinaryDescription

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

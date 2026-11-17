from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "ha_emivasa"

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="latest_reading",
        name="Water Meter Reading",
        icon="mdi:counter",
        native_unit_of_measurement="m³",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,  # Cumulative meter reading increases over time
    ),
    SensorEntityDescription(
        key="last_consumption",
        name="Daily Water Consumption",
        icon="mdi:water",
        native_unit_of_measurement="m³",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,  # Or MEASUREMENT for discrete daily consumption blocks
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HA Emivasa sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EmivasaSensor(coordinator, entry, description)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class EmivasaSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Emivasa Sensor."""

    def __init__(self, coordinator, entry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_name = f"HA Emivasa {description.name}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": f"HA Emivasa Water ({entry.data['username']})",
            "manufacturer": "Emivasa",
            "model": "Smart Water Meter",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        table = self.coordinator.data.get("table", [])
        if not table:
            return None

        # Get the latest entry in the table list
        latest = table[-1]

        if self.entity_description.key == "latest_reading":
            val_str = latest.get("Lectura", "0")
            if val_str:
                return float(str(val_str).replace(",", "."))
        elif self.entity_description.key == "last_consumption":
            val_str = latest.get("Consumo", "0")
            if val_str:
                return float(str(val_str).replace(",", "."))

        return None
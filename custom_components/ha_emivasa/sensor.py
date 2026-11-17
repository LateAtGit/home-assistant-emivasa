from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "ha_emivasa"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HA Emivasa sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EmivasaWaterReadingSensor(coordinator, entry),
        EmivasaWaterConsumptionSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class EmivasaBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor class for HA Emivasa."""

    def __init__(self, coordinator, entry) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": f"HA Emivasa Water ({entry.data['username']})",
            "manufacturer": "Emivasa",
            "model": "Smart Water Meter",
        }


class EmivasaWaterReadingSensor(EmivasaBaseSensor):
    """Sensor for the latest meter reading (total progressive)."""

    def __init__(self, coordinator, entry) -> None:
        """Initialize the meter reading sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_latest_reading"
        self._attr_name = "HA Emivasa Water Meter Reading"
        self._attr_icon = "mdi:counter"
        self._attr_native_unit_of_measurement = "m³"
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        """Return the state of the sensor."""
        table = self.coordinator.data.get("table", [])
        if not table:
            return None
        latest = table[-1]
        val_str = latest.get("Lectura", "0")
        if val_str:
            return float(str(val_str).replace(",", "."))
        return None


class EmivasaWaterConsumptionSensor(EmivasaBaseSensor):
    """Sensor for the latest daily consumption."""

    def __init__(self, coordinator, entry) -> None:
        """Initialize the daily consumption sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_last_consumption"
        self._attr_name = "HA Emivasa Daily Water Consumption"
        self._attr_icon = "mdi:water"
        self._attr_native_unit_of_measurement = "m³"
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self):
        """Return the state of the sensor."""
        table = self.coordinator.data.get("table", [])
        if not table:
            return None
        latest = table[-1]
        val_str = latest.get("Consumo", "0")
        if val_str:
            return float(str(val_str).replace(",", "."))
        return None
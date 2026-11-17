from homeassistant.components.sensor import SensorEntity
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
        EmivasaLatestReadingSensor(coordinator, entry),
        EmivasaLastConsumptionSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class EmivasaBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor class for HA Emivasa."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_{self.entity_description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": f"HA Emivasa Water ({entry.data['username']})",
            "manufacturer": "Emivasa",
            "model": "Smart Water Meter",
        }


class EmivasaLatestReadingSensor(EmivasaBaseSensor):
    """Sensor for the latest meter reading."""

    class entity_description:
        key = "latest_reading"
        name = "Water Meter Reading"
        icon = "mdi:counter"
        native_unit_of_measurement = "m³"

    def __init__(self, coordinator, entry) -> None:
        self.entity_description = self.__class__.entity_description
        super().__init__(coordinator, entry)
        self._attr_name = "HA Emivasa Water Meter Reading"
        self._attr_icon = self.entity_description.icon
        self._attr_native_unit_of_measurement = self.entity_description.native_unit_of_measurement

    @property
    def native_value(self):
        """Return the state of the sensor."""
        table = self.coordinator.data.get("table", [])
        if table:
            latest = table[-1]
            return float(latest.get("Lectura", "0").replace(",", "."))
        return None


class EmivasaLastConsumptionSensor(EmivasaBaseSensor):
    """Sensor for the latest daily consumption."""

    class entity_description:
        key = "last_consumption"
        name = "Daily Water Consumption"
        icon = "mdi:water"
        native_unit_of_measurement = "m³"

    def __init__(self, coordinator, entry) -> None:
        self.entity_description = self.__class__.entity_description
        super().__init__(coordinator, entry)
        self._attr_name = "HA Emivasa Daily Water Consumption"
        self._attr_icon = self.entity_description.icon
        self._attr_native_unit_of_measurement = self.entity_description.native_unit_of_measurement

    @property
    def native_value(self):
        """Return the state of the sensor."""
        table = self.coordinator.data.get("table", [])
        if table:
            latest = table[-1]
            return float(latest.get("Consumo", "0").replace(",", "."))
        return None
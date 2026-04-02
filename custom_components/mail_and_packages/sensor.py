"""Based on @skalavala work.

https://blog.kalavala.net/usps/homeassistant/mqtt/2018/01/12/usps.html
Configuration code contribution from @firstof9 https://github.com/firstof9/
"""
import datetime
from datetime import timezone
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_RESOURCES
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AMAZON_EXCEPTION_ORDER,
    AMAZON_ORDER,
    ATTR_ORDER,
    ATTR_TRACKING_NUM,
    COORDINATOR,
    DOMAIN,
    SENSOR_TYPES,
    VERSION,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    sensors = []
    resources = entry.data[CONF_RESOURCES]

    for variable in resources:
        if variable in SENSOR_TYPES:
            sensors.append(PackagesSensor(entry, SENSOR_TYPES[variable], coordinator))

    async_add_entities(sensors, False)


class PackagesSensor(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        config: ConfigEntry,
        sensor_description: SensorEntityDescription,
        coordinator,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = sensor_description
        self.coordinator = coordinator
        self._config = config
        self._name = sensor_description.name
        self.type = sensor_description.key
        self._host = config.data[CONF_HOST]
        self._unique_id = self._config.entry_id
        self.data = self.coordinator.data

    @property
    def device_info(self) -> dict:
        """Return device information about the mailbox."""
        return {
            "connections": {(DOMAIN, self._unique_id)},
            "name": self._host,
            "manufacturer": "IMAP E-Mail",
            "sw_version": VERSION,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return f"{self._host}_{self._name}_{self._unique_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.type in self.coordinator.data:
            if self.type == "mail_updated":
                return datetime.datetime.now(timezone.utc)
            return self.coordinator.data[self.type]
        return None

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> Optional[dict]:
        """Return device specific state attributes."""
        attr = {}
        data = self.coordinator.data

        if self.data is None:
            return attr

        # Tracking key based on sensorname
        tracking = f"{'_'.join(self.type.split('_')[:-1])}_tracking"

        # Amazon order attributes
        if self.type == "amazon_exception":
            if AMAZON_EXCEPTION_ORDER in data:
                attr[ATTR_ORDER] = data[AMAZON_EXCEPTION_ORDER]

        elif self.type.startswith("amazon_"):
            if AMAZON_ORDER in data:
                attr[ATTR_ORDER] = data[AMAZON_ORDER]

        # For all *_delivering sensors add tracking if applicable
        if self.type.endswith("_delivering") and tracking in data:
            attr[ATTR_TRACKING_NUM] = data[tracking]

        return attr

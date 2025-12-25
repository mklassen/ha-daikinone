from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import PERCENTAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.daikinone import DOMAIN, DaikinOneData
from custom_components.daikinone.daikinone import DaikinThermostat, DaikinHumidityLimit, DaikinThermostatCapability
from custom_components.daikinone.entity import DaikinOneEntity
from custom_components.daikinone.const import CONF_OPTION_ENTITY_UID_SCHEMA_VERSION_KEY


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daikin One select entities"""
    data: DaikinOneData = hass.data[DOMAIN]
    thermostats = data.daikin.get_thermostats().values()

    entities: list[NumberEntity] = []
    for thermostat in thermostats:
        if thermostat.capabilities & DaikinThermostatCapability.HUMIDIFY:
            entities += [
                DaikinOneHumidifyNumber(
                    description=NumberEntityDescription(
                        key="humidify",
                        name="Humidify Set Point",
                        has_entity_name=True,
                        icon="mdi:water-percent",
                        unit_of_measurement=PERCENTAGE,
                        native_step=DaikinHumidityLimit.STEP.value,
                        native_max_value=DaikinHumidityLimit.MAX.value - DaikinHumidityLimit.RANGE_MIN.value,
                        native_min_value=DaikinHumidityLimit.MIN.value,
                    ),
                    data=data,
                    thermostat=thermostat,
                ),
                DaikinOneDehumidifyNumber(
                    description=NumberEntityDescription(
                        key="dehumidify",
                        name="Dehumidify Set Point",
                        has_entity_name=True,
                        icon="mdi:water-percent",
                        unit_of_measurement=PERCENTAGE,
                        native_step=DaikinHumidityLimit.STEP.value,
                        native_max_value=DaikinHumidityLimit.MAX.value,
                        native_min_value=DaikinHumidityLimit.MIN.value + DaikinHumidityLimit.RANGE_MIN.value,
                    ),
                )
            ]

    async_add_entities(entities, True)


class DaikinOneHumidityNumber(DaikinOneEntity[DaikinThermostat], NumberEntity):
    _attr_native_step = DaikinHumidityLimit.STEP.value
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, description: NumberEntityDescription, data: DaikinOneData, thermostat: DaikinThermostat):
        super().__init__(data, thermostat)

        self.entity_description = description

        match data.entry.data[CONF_OPTION_ENTITY_UID_SCHEMA_VERSION_KEY]:
            case 0 | 1:
                self._attr_unique_id = f"{self._device.id}-{self.entity_description.key}"
            case _:
                raise ValueError("unexpected entity uid schema version")

        self.update_entity_attributes()

    @property
    def device_name(self) -> str:
        return f"{self._device.name} Thermostat"

    async def _set_humidity(self, humidify, dehumidify):
        def update(t: DaikinThermostat):
            t.set_point_humidify = humidify
            t.set_point_dehumidify = dehumidify

        await self.update_state_optimistically(
            operation=lambda: self._data.daikin.set_thermostat_humidity_set_points(
                self._device.id,
                humidify=humidify,
                dehumidify=dehumidify,
            ),
            optimistic_update=update,
            check=lambda t: t.set_point_humidify == humidify and t.set_point_dehumidify == dehumidify,
        )

    async def async_get_device(self) -> DaikinThermostat:
        return self._data.daikin.get_thermostat(self._device.id)

    def _clamp(self, value: float) -> float:
        # Ensure the requested set point is within limits
        value = max(self._attr_native_min_value, min(self._attr_native_max_value, value))

        # Ensure the requested set point has the correct step size
        value = round(value / self._attr_native_step) * self._attr_native_step
        return value


class DaikinOneHumidifyNumber(DaikinOneHumidityNumber):
    _attr_name = "Humidify"
    _attr_native_min_value = DaikinHumidityLimit.MIN.value
    _attr_native_max_value = (DaikinHumidityLimit.MAX.value - DaikinHumidityLimit.RANGE_MIN.value)

    async def async_set_native_value(self, value: float):
        humidify = self._clamp(value)

        # Ensure that the dehumidify set point is at least the minimum range above the requested humidify set point
        dehumidify = max(humidify + DaikinHumidityLimit.RANGE_MIN.value, self._device.set_point_dehumidify)

        await self._set_humidity(humidify, dehumidify)

    def update_entity_attributes(self) -> None:
        self._attr_native_value = self._device.set_point_humidify


class DaikinOneDehumidifyNumber(DaikinOneHumidityNumber):
    _attr_name = "Dehumidify"
    _attr_native_min_value = (DaikinHumidityLimit.MIN.value + DaikinHumidityLimit.RANGE_MIN.value)
    _attr_native_max_value = DaikinHumidityLimit.MAX.value

    async def async_set_native_value(self, value: float):
        dehumidify = self._clamp(value)

        # Ensure that the humidify set point is at least the minimum range below the requested dehumidify set point
        humidify = min(dehumidify - DaikinHumidityLimit.RANGE_MIN.value, self._device.set_point_humidify)

        await self._set_humidity(humidify, dehumidify)

    def update_entity_attributes(self) -> None:
        self._attr_native_value = self._device.set_point_dehumidify

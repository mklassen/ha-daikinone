import logging
from typing import Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfTemperature,
    PERCENTAGE,
    UnitOfPower,
    UnitOfTime,
    UnitOfPressure,
    UnitOfElectricCurrent,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    REVOLUTIONS_PER_MINUTE,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from custom_components.daikinone import DOMAIN, DaikinOneData
from custom_components.daikinone.const import CONF_OPTION_ENTITY_UID_SCHEMA_VERSION_KEY, MANUFACTURER
from custom_components.daikinone.daikinone import (
    DaikinDevice,
    DaikinEEVCoil,
    DaikinOutdoorUnitReversingValveStatus,
    DaikinOutdoorUnitHeaterStatus,
    DaikinThermostat,
    DaikinIndoorUnit,
    DaikinEquipment,
    DaikinOutdoorUnit,
)

log = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daikin One sensors"""
    data: DaikinOneData = hass.data[DOMAIN]
    thermostats = data.daikin.get_thermostats().values()

    entities: list[SensorEntity] = []
    for thermostat in thermostats:
        # thermostat sensors

        entities += [
            DaikinOneThermostatSensor(
                description=SensorEntityDescription(
                    key="online",
                    name="Online Status",
                    has_entity_name=True,
                    device_class=SensorDeviceClass.ENUM,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:connection",
                ),
                data=data,
                device=thermostat,
                attribute=lambda d: "Online" if d.online else "Offline",
            ),
            DaikinOneThermostatSensor(
                description=SensorEntityDescription(
                    key="indoor_temperature",
                    name="Indoor Temperature",
                    has_entity_name=True,
                    state_class=SensorStateClass.MEASUREMENT,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    icon="mdi:thermometer",
                ),
                data=data,
                device=thermostat,
                attribute=lambda d: d.indoor_temperature.celsius,
            ),
            DaikinOneThermostatSensor(
                description=SensorEntityDescription(
                    key="indoor_humidity",
                    name="Indoor Humidity",
                    has_entity_name=True,
                    state_class=SensorStateClass.MEASUREMENT,
                    device_class=SensorDeviceClass.HUMIDITY,
                    native_unit_of_measurement=PERCENTAGE,
                    icon="mdi:water-percent",
                ),
                data=data,
                device=thermostat,
                attribute=lambda d: d.indoor_humidity,
            ),
        ]

        # equipment sensors
        for equipment in thermostat.equipment.values():
            match equipment:
                # air handler / furnance sensors
                case DaikinIndoorUnit():
                    entities += [
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="mode",
                                name="Mode",
                                has_entity_name=True,
                                device_class=SensorDeviceClass.ENUM,
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.mode,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="airflow",
                                name="Airflow",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_FEET_PER_MINUTE,
                                icon="mdi:fan",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.current_airflow,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="fan_demand_requested",
                                name="Fan Demand Requested",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:fan",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.fan_demand_requested_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="fan_demand_current",
                                name="Fan Demand Current",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:fan",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.fan_demand_current_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="heat_demand_requested",
                                name="Heat Demand Requested",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:heat-wave",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.heat_demand_requested_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="heat_demand_current",
                                name="Heat Demand Current",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:heat-wave",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.heat_demand_current_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="humidification_demand_requested",
                                name="Humidification Demand Requested",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:water-percent",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.humidification_demand_requested_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="power_usage",
                                name="Power Usage",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.POWER,
                                native_unit_of_measurement=UnitOfPower.WATT,
                                icon="mdi:meter-electric",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.power_usage,
                        ),
                    ]

                    # optional indoor unit sensors
                    if equipment.cool_demand_requested_percent is not None:
                        entities.append(
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="cool_demand_requested",
                                    name="Cool Demand Requested",
                                    has_entity_name=True,
                                    state_class=SensorStateClass.MEASUREMENT,
                                    native_unit_of_measurement=PERCENTAGE,
                                    icon="mdi:snowflake-thermometer",
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.cool_demand_requested_percent,
                            )
                        )

                    if equipment.cool_demand_current_percent is not None:
                        entities.append(
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="cool_demand_current",
                                    name="Cool Demand Current",
                                    has_entity_name=True,
                                    state_class=SensorStateClass.MEASUREMENT,
                                    native_unit_of_measurement=PERCENTAGE,
                                    icon="mdi:snowflake-thermometer",
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.cool_demand_current_percent,
                            )
                        )

                    if equipment.dehumidification_demand_requested_percent is not None:
                        entities.append(
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="dehumidification_demand_requested",
                                    name="Dehumidification Demand Requested",
                                    has_entity_name=True,
                                    state_class=SensorStateClass.MEASUREMENT,
                                    native_unit_of_measurement=PERCENTAGE,
                                    icon="mdi:air-humidifier",
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.dehumidification_demand_requested_percent,
                            )
                        )

                # outdoor unit sensors
                case DaikinOutdoorUnit():
                    entities += [
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="total_runtime",
                                name="Total Runtime",
                                has_entity_name=True,
                                state_class=SensorStateClass.TOTAL_INCREASING,
                                device_class=SensorDeviceClass.DURATION,
                                native_unit_of_measurement=UnitOfTime.SECONDS,
                                suggested_unit_of_measurement=UnitOfTime.HOURS,
                                icon="mdi:clock-time-ten-outline",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.total_runtime.total_seconds(),
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="mode",
                                name="Mode",
                                has_entity_name=True,
                                device_class=SensorDeviceClass.ENUM,
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.mode,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="compressor_speed_target",
                                name="Compressor Speed Target",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                                icon="mdi:heat-pump",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.compressor_speed_target,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="compressor_speed_current",
                                name="Compressor Speed",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                                icon="mdi:heat-pump",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.compressor_speed_current,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="outdoor_fan_speed",
                                name="Outdoor Fan Speed",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                                icon="mdi:fan",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.outdoor_fan_rpm,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="outdoor_fan_target",
                                name="Outdoor Fan Target Speed",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                                icon="mdi:fan",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.outdoor_fan_target_rpm,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="suction_pressure",
                                name="Suction Pressure",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.PRESSURE,
                                native_unit_of_measurement=UnitOfPressure.PSI,
                                icon="mdi:pipe",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.suction_pressure_psi,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="eev_opening",
                                name="EEV Opening",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:valve",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.eev_opening_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="heat_demand",
                                name="Heat Demand",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:sun-thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.heat_demand_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="cool_demand",
                                name="Cool Demand",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:snowflake-thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.cool_demand_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="fan_demand",
                                name="Fan Demand",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:air-filter",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.fan_demand_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="fan_airflow_demand",
                                name="Fan Airflow Demand",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_FEET_PER_MINUTE,
                                icon="mdi:air-filter",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.fan_demand_airflow,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="dehumidify_demand",
                                name="Dehumidify Demand",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:air-humidifier",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.dehumidify_demand_percent,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="air_temperature",
                                name="Air Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.air_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="coil_temperature",
                                name="Coil Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.coil_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="discharge_temperature",
                                name="Discharge Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.discharge_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="liquid_temperature",
                                name="Liquid Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.liquid_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="defrost_sensor_temperature",
                                name="Defrost Sensor Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.defrost_sensor_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="inverter_fin_temperature",
                                name="Inverter Fin Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.inverter_fin_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="power_usage",
                                name="Power Usage",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.POWER,
                                native_unit_of_measurement=UnitOfPower.WATT,
                                icon="mdi:meter-electric",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.power_usage,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="compressor_current",
                                name="Compressor Current",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.CURRENT,
                                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                                icon="mdi:meter-electric",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.compressor_amps,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="inverter_current",
                                name="Inverter Current",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.CURRENT,
                                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                                icon="mdi:meter-electric",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.inverter_amps,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="fan_motor_current",
                                name="Fan Motor Current",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.CURRENT,
                                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                                icon="mdi:meter-electric",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.fan_motor_amps,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="outdoor_temperature",
                                name="Outdoor Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.outdoor_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="outdoor_humidity",
                                name="Outdoor Humidity",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.HUMIDITY,
                                native_unit_of_measurement=PERCENTAGE,
                                icon="mdi:water-percent",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.outdoor_humidity,
                        ),
                    ]

                    if equipment.outdoor_air_quality_available:
                        entities.extend([
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="outdoor_air_quality_index",
                                    name="Outdoor Air Quality Index",
                                    has_entity_name=True,
                                    state_class=SensorStateClass.MEASUREMENT,
                                    device_class=SensorDeviceClass.AQI,
                                    icon="mdi:air-filter",
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.outdoor_air_quality_index,
                            ),
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="outdoor_air_quality_particles",
                                    name="Outdoor Air Quality Particles",
                                    has_entity_name=True,
                                    state_class=SensorStateClass.MEASUREMENT,
                                    device_class=SensorDeviceClass.PM25,
                                    native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                                    icon="mdi:air-filter",
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.outdoor_air_quality_particles,
                            ),
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="outdoor_air_quality_ozone",
                                    name="Outdoor Air Quality Ozone",
                                    has_entity_name=True,
                                    state_class=SensorStateClass.MEASUREMENT,
                                    device_class=SensorDeviceClass.OZONE,
                                    native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                                    icon="mdi:molecule",
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.outdoor_air_quality_ozone,
                            ),
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="outdoor_air_quality_level",
                                    name="Outdoor Air Quality Level",
                                    has_entity_name=True,
                                    state_class=SensorStateClass.MEASUREMENT,
                                    device_class=SensorDeviceClass.ENUM,
                                    native_unit_of_measurement=None,
                                    icon="mdi:air-filter",
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.outdoor_air_quality_level,
                            ),
                        ])

                    # optional outdoor unit sensors
                    if equipment.reversing_valve is not DaikinOutdoorUnitReversingValveStatus.UNKNOWN:
                        entities.append(
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="reversing_valve",
                                    name="Reversing Valve",
                                    has_entity_name=True,
                                    device_class=SensorDeviceClass.ENUM,
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.reversing_valve.name.capitalize(),
                            )
                        )

                    if equipment.crank_case_heater is not DaikinOutdoorUnitHeaterStatus.UNKNOWN:
                        entities.append(
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="crank_case_heater",
                                    name="Crrank Case Heater",
                                    has_entity_name=True,
                                    device_class=SensorDeviceClass.ENUM,
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.crank_case_heater.name.capitalize(),
                            )
                        )

                    if equipment.drain_pan_heater is not DaikinOutdoorUnitHeaterStatus.UNKNOWN:
                        entities.append(
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="drain_pan_heater",
                                    name="Drain Pan Heater",
                                    has_entity_name=True,
                                    device_class=SensorDeviceClass.ENUM,
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.drain_pan_heater.name.capitalize(),
                            )
                        )

                    if equipment.preheat_heater is not DaikinOutdoorUnitHeaterStatus.UNKNOWN:
                        entities.append(
                            DaikinOneEquipmentSensor(
                                description=SensorEntityDescription(
                                    key="preheat_heater",
                                    name="Preheat",
                                    has_entity_name=True,
                                    device_class=SensorDeviceClass.ENUM,
                                ),
                                data=data,
                                device=equipment,
                                attribute=lambda e: e.preheat_heater.name.capitalize(),
                            )
                        )

                case DaikinEEVCoil():
                    entities += [
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="indoor_superheat_temperature",
                                name="Indoor Superheat Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.indoor_superheat_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="liquid_temperature",
                                name="Liquid Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.liquid_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="suction_temperature",
                                name="Suction Temperature",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.TEMPERATURE,
                                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                                icon="mdi:thermometer",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.suction_temperature.celsius,
                        ),
                        DaikinOneEquipmentSensor(
                            description=SensorEntityDescription(
                                key="pressure",
                                name="Pressure",
                                has_entity_name=True,
                                state_class=SensorStateClass.MEASUREMENT,
                                device_class=SensorDeviceClass.PRESSURE,
                                native_unit_of_measurement=UnitOfPressure.PSI,
                                icon="mdi:pipe",
                            ),
                            data=data,
                            device=equipment,
                            attribute=lambda e: e.pressure_psi,
                        ),
                    ]

                case _:
                    log.warning(f"unexpected equipment: {equipment}")

    async_add_entities(entities, True)


class DaikinOneSensor[D: DaikinDevice](SensorEntity):
    def __init__(
        self, description: SensorEntityDescription, data: DaikinOneData, device: D, attribute: Callable[[D], StateType]
    ) -> None:
        """Initialize the sensor."""

        self.entity_description = description
        self._data = data
        self._device: D = device
        self._attribute = attribute

        self._attr_device_info = self.get_device_info()

    def get_device_info(self) -> DeviceInfo | None:
        """Return device information for this sensor."""

        info = DeviceInfo(
            identifiers={(DOMAIN, self._device.id)},
            name=self.device_name,
            manufacturer=MANUFACTURER,
            model=self._device.model,
            sw_version=self._device.firmware_version,
        )

        if self.device_parent is not None:
            info["via_device"] = (DOMAIN, self.device_parent)

        return info

    @property
    def device_name(self) -> str:
        """Return the name of the device."""
        raise NotImplementedError("Sensor subclass did not implement device_name")

    @property
    def device_parent(self) -> str | None:
        """Return the name of the device."""
        return None


class DaikinOneThermostatSensor(DaikinOneSensor[DaikinThermostat]):
    def __init__(
        self,
        description: SensorEntityDescription,
        data: DaikinOneData,
        device: DaikinThermostat,
        attribute: Callable[[DaikinThermostat], StateType],
    ) -> None:
        super().__init__(description, data, device, attribute)

        match data.entry.data[CONF_OPTION_ENTITY_UID_SCHEMA_VERSION_KEY]:
            case 0:
                self._attr_unique_id = f"{self._device.id}-{self.name}"
            case 1:
                self._attr_unique_id = f"{self._device.id}-{self.entity_description.key}"
            case _:
                raise ValueError("unexpected entity uid schema version")

    @property
    def device_name(self) -> str:
        return f"{self._device.name} Thermostat"

    async def async_update(self) -> None:
        """Get the latest state of the sensor."""
        await self._data.update()
        self._device = self._data.daikin.get_thermostat(self._device.id)
        self._attr_native_value = self._attribute(self._device)


class DaikinOneEquipmentSensor[E: DaikinEquipment](DaikinOneSensor[E]):
    def __init__(
        self, description: SensorEntityDescription, data: DaikinOneData, device: E, attribute: Callable[[E], StateType]
    ) -> None:
        super().__init__(description, data, device, attribute)

        match data.entry.data[CONF_OPTION_ENTITY_UID_SCHEMA_VERSION_KEY]:
            case 0:
                self._attr_unique_id = f"{self._device.id}-{self.name}"
            case 1:
                self._attr_unique_id = f"{self._device.thermostat_id}-{self._device.id}-{self.entity_description.key}"
            case _:
                raise ValueError("unexpected entity uid schema version")

    @property
    def device_name(self) -> str:
        thermostat = self._data.daikin.get_thermostat(self._device.thermostat_id)
        return f"{thermostat.name} {self._device.name}"

    async def async_update(self) -> None:
        """Get the latest state of the sensor."""
        await self._data.update()
        thermostat = self._data.daikin.get_thermostat(self._device.thermostat_id)
        self._device = thermostat.equipment[self._device.id]
        self._attr_native_value = self._attribute(self._device)

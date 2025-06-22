"""
Management command to initialize the database with sample data.
"""

import random
from datetime import timedelta

import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from django_backend.apps.core.models import (Scenario, TurbineMeasurement,
                                             WeatherData, WindTurbine)


class Command(BaseCommand):
    help = "Initialize the database with sample data"

    def handle(self, *args, **options):
        self.stdout.write("Initializing database with sample data...")

        with transaction.atomic():
            self._create_turbines()
            self._create_scenarios()
            self._create_sample_data()

        self.stdout.write(self.style.SUCCESS("Successfully initialized database"))

    def _create_turbines(self):
        """Create sample wind turbines"""
        self.stdout.write("Creating wind turbines...")

        # Delete existing turbines
        WindTurbine.objects.all().delete()

        # Create new turbines
        turbines = [
            WindTurbine(
                name="Turbine 1",
                hub_height=135.0,
                rotor_diameter=101.0,
                nominal_power=3.05e6,
                status="operational",
                latitude=52.2297,
                longitude=21.0122,
            ),
            WindTurbine(
                name="Turbine 2",
                hub_height=135.0,
                rotor_diameter=101.0,
                nominal_power=3.05e6,
                status="operational",
                latitude=52.2298,
                longitude=21.0124,
            ),
            WindTurbine(
                name="Turbine 3",
                hub_height=135.0,
                rotor_diameter=101.0,
                nominal_power=3.05e6,
                status="operational",
                latitude=52.2299,
                longitude=21.0126,
            ),
            WindTurbine(
                name="Turbine 4",
                hub_height=135.0,
                rotor_diameter=101.0,
                nominal_power=3.05e6,
                status="maintenance",
                latitude=52.2300,
                longitude=21.0128,
            ),
            WindTurbine(
                name="Turbine 5",
                hub_height=135.0,
                rotor_diameter=101.0,
                nominal_power=3.05e6,
                status="operational",
                latitude=52.2301,
                longitude=21.0130,
            ),
        ]

        WindTurbine.objects.bulk_create(turbines)
        self.stdout.write(f"Created {len(turbines)} wind turbines")

    def _create_scenarios(self):
        """Create sample scenarios"""
        self.stdout.write("Creating scenarios...")

        # Delete existing scenarios
        Scenario.objects.all().delete()

        # Create new scenarios
        scenarios = [
            Scenario(
                name="Normal Operation",
                description="Normal wind farm operation with typical wind conditions",
                scenario_type="normal_operation",
                active=True,
                parameters={},
            ),
            Scenario(
                name="Grid Fault",
                description="Simulation of a grid fault with voltage dip",
                scenario_type="grid_fault",
                active=False,
                parameters={"voltage": 0.7, "duration": 0.2},
            ),
            Scenario(
                name="Turbine Failure",
                description="Simulation of a mechanical failure in a specific turbine",
                scenario_type="turbine_failure",
                active=False,
                parameters={"turbine_id": 3},
            ),
            Scenario(
                name="Storm Conditions",
                description="Simulation of storm conditions with high wind speeds",
                scenario_type="storm",
                active=False,
                parameters={"wind_speed": 20.0},
            ),
        ]

        Scenario.objects.bulk_create(scenarios)
        self.stdout.write(f"Created {len(scenarios)} scenarios")

    def _create_sample_data(self):
        """Create sample weather and measurement data"""
        self.stdout.write("Creating sample data...")

        # Delete existing data
        WeatherData.objects.all().delete()
        TurbineMeasurement.objects.all().delete()

        # Get turbines
        turbines = WindTurbine.objects.all()

        # Create data for the last 24 hours
        now = timezone.now()
        start_time = now - timedelta(hours=24)

        # Create weather data
        weather_data = []

        for i in range(288):  # 5-minute intervals for 24 hours
            timestamp = start_time + timedelta(minutes=5 * i)

            # Base wind speed with some variation over time (simulating a realistic pattern)
            hour_of_day = timestamp.hour
            base_wind_speed = 5.0 + 3.0 * np.sin(np.pi * hour_of_day / 12.0)

            wind_speed = max(0, base_wind_speed + random.normalvariate(0, 0.8))  # nosec
            wind_direction = random.uniform(0, 360)  # nosec
            temperature = (
                15.0
                + 5.0 * np.sin(np.pi * hour_of_day / 12.0)
                + random.normalvariate(0, 1.0)
            )
            pressure = 1013.0 + random.normalvariate(0, 2.0)
            humidity = min(100, max(0, 70.0 + random.normalvariate(0, 3.0)))

            weather_data.append(
                WeatherData(
                    timestamp=timestamp,
                    wind_speed=wind_speed,
                    wind_direction=wind_direction,
                    temperature=temperature,
                    pressure=pressure,
                    humidity=humidity,
                )
            )

        WeatherData.objects.bulk_create(weather_data)
        self.stdout.write(f"Created {len(weather_data)} weather data points")

        # Create turbine measurements
        measurements = []

        for turbine in turbines:
            for i in range(288):  # 5-minute intervals for 24 hours
                timestamp = start_time + timedelta(minutes=5 * i)

                # Get corresponding weather data
                weather = weather_data[i]

                # Calculate power output based on wind speed and turbine status
                if turbine.status == "operational":
                    # Simple power curve approximation
                    wind_speed = weather.wind_speed

                    if wind_speed < 3.0:
                        power_output = 0.0
                    elif wind_speed < 12.0:
                        # Cubic relationship between wind speed and power
                        power_factor = ((wind_speed - 3.0) / 9.0) ** 3
                        power_output = turbine.nominal_power * power_factor
                    else:
                        power_output = turbine.nominal_power

                    # Add some random variation
                    power_output *= 0.95 + random.normalvariate(0, 0.03)
                else:
                    power_output = 0.0

                # Calculate other parameters
                if turbine.status == "operational":
                    if wind_speed < 3.0:
                        rotor_speed = 0.0
                    elif wind_speed < 12.0:
                        rotor_speed = 5.0 + (wind_speed - 3.0) * 1.2
                    else:
                        rotor_speed = 15.0

                    if wind_speed < 12.0:
                        blade_pitch = 0.0
                    else:
                        blade_pitch = min(45.0, (wind_speed - 12.0) * 5.0)
                else:
                    rotor_speed = 0.0
                    blade_pitch = 0.0

                measurements.append(
                    TurbineMeasurement(
                        turbine=turbine,
                        timestamp=timestamp,
                        power_output=power_output,
                        wind_speed=wind_speed,
                        rotor_speed=rotor_speed,
                        blade_pitch=blade_pitch,
                        nacelle_orientation=weather.wind_direction,
                        grid_voltage=400.0 + random.normalvariate(0, 2.0),
                        grid_frequency=50.0 + random.normalvariate(0, 0.01),
                    )
                )

        # Batch insert in chunks to avoid memory issues
        chunk_size = 1000
        for i in range(0, len(measurements), chunk_size):
            TurbineMeasurement.objects.bulk_create(measurements[i : i + chunk_size])

        self.stdout.write(f"Created {len(measurements)} turbine measurements")

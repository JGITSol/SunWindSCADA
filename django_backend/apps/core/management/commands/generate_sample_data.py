"""
Management command to generate sample data from the template.
This provides more flexibility than the initialize_data command by using the template.
"""

import json
import os
import random
from datetime import timedelta

import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from django_backend.apps.core.models import (GridComplianceCheck, Scenario,
                                             TurbineMeasurement, WeatherData,
                                             WindTurbine)


class Command(BaseCommand):
    help = "Generate sample data from the template"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours", type=int, default=24, help="Number of hours of data to generate"
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Interval in minutes between data points",
        )
        parser.add_argument(
            "--pattern",
            type=str,
            choices=["summer", "winter", "spring", "autumn", "random"],
            default="random",
            help="Weather pattern to use",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean existing data before generating new data",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        interval = options["interval"]
        pattern = options["pattern"]
        clean = options["clean"]

        self.stdout.write(
            f"Generating {hours} hours of data with {interval}-minute intervals using {pattern} pattern"
        )

        # Load template
        template_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "templates",
            "sample_data.json",
        )

        try:
            with open(template_path, "r") as f:
                self.template = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading template: {e}"))
            return

        with transaction.atomic():
            if clean:
                self.clean_data()

            self.create_turbines()
            self.create_scenarios()
            self.generate_data(hours, interval, pattern)

        self.stdout.write(self.style.SUCCESS("Successfully generated sample data"))

    def clean_data(self):
        """Clean existing data"""
        self.stdout.write("Cleaning existing data...")
        TurbineMeasurement.objects.all().delete()
        WeatherData.objects.all().delete()
        GridComplianceCheck.objects.all().delete()
        Scenario.objects.all().delete()
        WindTurbine.objects.all().delete()

    def create_turbines(self):
        """Create turbines from template"""
        self.stdout.write("Creating turbines...")

        turbines = []
        for turbine_data in self.template["turbines"]:
            turbines.append(
                WindTurbine(
                    name=turbine_data["name"],
                    hub_height=turbine_data["hub_height"],
                    rotor_diameter=turbine_data["rotor_diameter"],
                    nominal_power=turbine_data["nominal_power"],
                    status=turbine_data["status"],
                    latitude=turbine_data.get("latitude"),
                    longitude=turbine_data.get("longitude"),
                )
            )

        WindTurbine.objects.bulk_create(turbines)
        self.stdout.write(f"Created {len(turbines)} turbines")

    def create_scenarios(self):
        """Create scenarios from template"""
        self.stdout.write("Creating scenarios...")

        scenarios = []
        for scenario_data in self.template["scenarios"]:
            scenarios.append(
                Scenario(
                    name=scenario_data["name"],
                    description=scenario_data["description"],
                    scenario_type=scenario_data["scenario_type"],
                    active=scenario_data["active"],
                    parameters=scenario_data["parameters"],
                )
            )

        Scenario.objects.bulk_create(scenarios)
        self.stdout.write(f"Created {len(scenarios)} scenarios")

    def generate_data(self, hours, interval, pattern_name):
        """Generate time series data"""
        self.stdout.write("Generating time series data...")

        # Get turbines
        turbines = WindTurbine.objects.all()

        # Select weather pattern
        if pattern_name == "random":
            pattern = random.choice(self.template["weather_patterns"])  # nosec
        else:
            patterns = {p["name"].lower(): p for p in self.template["weather_patterns"]}
            pattern = patterns.get(
                pattern_name,
                next(
                    (
                        p
                        for p in self.template["weather_patterns"]
                        if pattern_name in p["name"].lower()
                    ),
                    self.template["weather_patterns"][0],
                ),
            )

        self.stdout.write(f'Using weather pattern: {pattern["name"]}')

        # Create data for the specified time period
        now = timezone.now()
        start_time = now - timedelta(hours=hours)

        # Number of data points
        num_points = int(hours * 60 / interval)

        # Create weather data
        weather_data = []

        for i in range(num_points):
            timestamp = start_time + timedelta(minutes=interval * i)

            # Generate wind speed based on pattern
            hour_of_day = timestamp.hour
            if pattern["wind_pattern"] == "diurnal":
                # Higher winds during day, lower at night
                base_wind_speed = pattern["base_wind_speed"] + 2.0 * np.sin(
                    np.pi * hour_of_day / 12.0
                )
            elif pattern["wind_pattern"] == "increasing":
                # Wind speed increases over time
                base_wind_speed = pattern["base_wind_speed"] + 0.1 * i
            elif pattern["wind_pattern"] == "gusty":
                # More variable wind
                base_wind_speed = pattern["base_wind_speed"] + 3.0 * np.sin(0.1 * i)
            else:  # steady
                base_wind_speed = pattern["base_wind_speed"]

            # Add random variation
            wind_speed = max(0, base_wind_speed + random.normalvariate(0, 1.0))  # nosec
            wind_direction = random.uniform(0, 360)  # nosec

            # Temperature varies with time of day
            temp_min, temp_max = pattern["temperature_range"]
            temperature = (
                temp_min
                + (temp_max - temp_min) * np.sin(np.pi * hour_of_day / 12.0) ** 2
            )
            temperature += random.normalvariate(0, 0.5)

            # Pressure and humidity
            pressure = pattern.get("pressure", 1013.0) + random.normalvariate(0, 1.0)

            humidity_min, humidity_max = pattern["humidity_range"]
            humidity = humidity_min + (humidity_max - humidity_min) * random.random()  # nosec

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

        # Batch insert weather data
        WeatherData.objects.bulk_create(weather_data)
        self.stdout.write(f"Created {len(weather_data)} weather data points")

        # Create turbine measurements
        all_measurements = []

        # Get power curves from template
        power_curves = self.template["power_curves"]

        for turbine in turbines:
            # Find matching power curve or use first one
            power_curve = power_curves.get(
                turbine.name, next(iter(power_curves.values()))
            )

            wind_speeds = np.array(power_curve["wind_speeds"])
            power_values = np.array(power_curve["power_values"])

            for i in range(num_points):
                timestamp = start_time + timedelta(minutes=interval * i)

                # Get corresponding weather data
                weather = weather_data[i]

                # Calculate power output based on wind speed and turbine status
                if turbine.status == "operational":
                    # Use power curve to calculate power
                    wind_speed = weather.wind_speed
                    power_output = np.interp(wind_speed, wind_speeds, power_values)

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

                all_measurements.append(
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

        # Batch insert measurements in chunks to avoid memory issues
        chunk_size = 1000
        for i in range(0, len(all_measurements), chunk_size):
            TurbineMeasurement.objects.bulk_create(all_measurements[i : i + chunk_size])

        self.stdout.write(f"Created {len(all_measurements)} turbine measurements")

        # Generate some grid compliance checks
        self.generate_compliance_checks(turbines, hours)

    def generate_compliance_checks(self, turbines, hours):
        """Generate some grid compliance checks"""
        self.stdout.write("Generating grid compliance checks...")

        # Get LVRT and HVRT curves from template
        grid_compliance = self.template["grid_compliance"]
        lvrt_curve = grid_compliance["lvrt_curve"]
        hvrt_curve = grid_compliance["hvrt_curve"]

        # Generate random grid events
        now = timezone.now()
        num_events = random.randint(3, 10)  # Random number of events  # nosec

        compliance_checks = []

        for _ in range(num_events):
            # Random timestamp within the period
            timestamp = now - timedelta(hours=random.uniform(0, hours))  # nosec

            # Random check type
            check_type = random.choice(["lvrt", "hvrt", "frequency", "reactive_power"])  # nosec

            # Random turbine
            turbine = random.choice(turbines)  # nosec

            if check_type == "lvrt":
                # Random voltage between 0 and 0.9 p.u.
                voltage_pu = random.uniform(0.0, 0.9)  # nosec

                # Get maximum allowed duration from curve
                max_duration = np.interp(
                    voltage_pu, lvrt_curve["voltage_pu"], lvrt_curve["duration_seconds"]
                )

                # Random duration, sometimes exceeding the limit
                if random.random() < 0.8:  # 80% compliant # nosec
                    duration = random.uniform(0, max_duration * 0.9) # nosec
                    compliant = True
                else:
                    duration = random.uniform(max_duration * 1.1, max_duration * 2.0) # nosec
                    compliant = False

                compliance_checks.append(
                    GridComplianceCheck(
                        turbine=turbine,
                        timestamp=timestamp,
                        check_type=check_type,
                        voltage_pu=voltage_pu,
                        duration=duration,
                        compliant=compliant,
                        details={
                            "event_type": "voltage_dip",
                            "max_allowed_duration": float(max_duration),
                        },
                    )
                )

            elif check_type == "hvrt":
                # Random voltage between 1.1 and 1.2 p.u.
                voltage_pu = random.uniform(1.1, 1.2)  # nosec

                # Get maximum allowed duration from curve
                max_duration = np.interp(
                    voltage_pu, hvrt_curve["voltage_pu"], hvrt_curve["duration_seconds"]
                )

                # Random duration, sometimes exceeding the limit
                if random.random() < 0.8:  # 80% compliant # nosec
                    duration = random.uniform(0, max_duration * 0.9)# nosec
                    compliant = True
                else:
                    duration = random.uniform(max_duration * 1.1, max_duration * 2.0)# nosec
                    compliant = False

                compliance_checks.append(
                    GridComplianceCheck(
                        turbine=turbine,
                        timestamp=timestamp,
                        check_type=check_type,
                        voltage_pu=voltage_pu,
                        duration=duration,
                        compliant=compliant,
                        details={
                            "event_type": "voltage_swell",
                            "max_allowed_duration": float(max_duration),
                        },
                    )
                )

            elif check_type == "frequency":
                # Random frequency deviation
                frequency = random.uniform(47.0, 52.0)  # nosec

                # Check compliance
                freq_limits = grid_compliance["frequency_limits"]
                if (
                    freq_limits["min_continuous"]
                    <= frequency
                    <= freq_limits["max_continuous"]
                ):
                    compliant = True
                    details = {"status": "within_continuous_limits"}
                elif (
                    freq_limits["min_temporary"]
                    <= frequency
                    <= freq_limits["max_temporary"]
                ):
                    compliant = True
                    details = {
                        "status": "within_temporary_limits",
                        "max_duration": freq_limits["temporary_duration"],
                    }
                else:
                    compliant = False
                    details = {"status": "outside_limits"}

                compliance_checks.append(
                    GridComplianceCheck(
                        turbine=turbine,
                        timestamp=timestamp,
                        check_type=check_type,
                        frequency=frequency,
                        compliant=compliant,
                        details=details,
                    )
                )

            elif check_type == "reactive_power":
                # Random voltage deviation
                voltage_pu = random.uniform(0.9, 1.1)  # nosec
                voltage_deviation = voltage_pu - 1.0

                # Always compliant for this example
                compliant = True

                compliance_checks.append(
                    GridComplianceCheck(
                        turbine=turbine,
                        timestamp=timestamp,
                        check_type=check_type,
                        voltage_pu=voltage_pu,
                        compliant=compliant,
                        details={
                            "voltage_deviation": float(voltage_deviation),
                            "required_reactive_power": float(2.0 * voltage_deviation),
                        },
                    )
                )

        # Create compliance checks
        GridComplianceCheck.objects.bulk_create(compliance_checks)
        self.stdout.write(f"Created {len(compliance_checks)} grid compliance checks")

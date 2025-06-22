from django.db import models


class WindTurbine(models.Model):
    """
    Model representing a wind turbine in the SCADA system.
    """

    name = models.CharField(max_length=100)
    hub_height = models.FloatField(help_text="Hub height in meters")
    rotor_diameter = models.FloatField(
        help_text="Rotor diameter in meters"
    )
    nominal_power = models.FloatField(help_text="Nominal power in W")
    status = models.CharField(
        max_length=32,
        default="operational",
        choices=[
            ("operational", "Operational"),
            ("maintenance", "Under Maintenance"),
            ("fault", "Fault"),
            ("offline", "Offline"),
        ],
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class WeatherData(models.Model):
    """
    Model for storing weather data relevant to wind power generation.
    """

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    wind_speed = models.FloatField(help_text="Wind speed in m/s")
    wind_direction = models.FloatField(
        help_text="Wind direction in degrees", null=True, blank=True
    )
    temperature = models.FloatField(
        help_text="Temperature in Celsius"
    )
    pressure = models.FloatField(
        help_text="Atmospheric pressure in hPa"
    )
    humidity = models.FloatField(help_text="Relative humidity in %")

    def __str__(self):
        return f"Weather data at {self.timestamp}"


class TurbineMeasurement(models.Model):
    """
    Model for storing real-time measurements from wind turbines.
    """

    turbine = models.ForeignKey(
        WindTurbine, on_delete=models.CASCADE, related_name="measurements", db_index=True
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    power_output = models.FloatField(help_text="Power output in W")
    wind_speed = models.FloatField(
        help_text="Local wind speed at turbine in m/s"
    )
    rotor_speed = models.FloatField(
        help_text="Rotor speed in rpm", null=True, blank=True
    )
    blade_pitch = models.FloatField(
        help_text="Blade pitch angle in degrees", null=True, blank=True
    )
    nacelle_orientation = models.FloatField(
        help_text="Nacelle orientation in degrees", null=True, blank=True
    )
    grid_voltage = models.FloatField(
        help_text="Grid voltage in V", null=True, blank=True
    )
    grid_frequency = models.FloatField(
        help_text="Grid frequency in Hz", null=True, blank=True
    )

    def __str__(self):
        return f"{self.turbine.name} measurement at {self.timestamp}"


class Scenario(models.Model):
    """
    Model for defining simulation scenarios (normal operation, grid fault, etc.)
    """

    name = models.CharField(max_length=100)
    description = models.TextField()
    active = models.BooleanField(default=False)
    scenario_type = models.CharField(
        max_length=50,
        choices=[
            ("normal_operation", "Normal Operation"),
            ("grid_fault", "Grid Fault"),
            ("turbine_failure", "Turbine Failure"),
            ("storm", "Storm Conditions"),
            ("custom", "Custom Scenario"),
        ],
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON parameters specific to the scenario type",
    )

    def __str__(self):
        return self.name


class GridComplianceCheck(models.Model):
    """
    Model for storing grid compliance check results (LVRT/HVRT).
    """

    turbine = models.ForeignKey(
        WindTurbine, on_delete=models.CASCADE, related_name="compliance_checks", db_index=True
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    check_type = models.CharField(
        max_length=20,
        choices=[
            ("lvrt", "Low Voltage Ride Through"),
            ("hvrt", "High Voltage Ride Through"),
            ("frequency", "Frequency Deviation"),
            ("reactive_power", "Reactive Power Support"),
        ],
    )
    voltage_pu = models.FloatField(
        help_text="Voltage in per-unit", null=True, blank=True
    )
    duration = models.FloatField(
        help_text="Event duration in seconds", null=True, blank=True
    )
    frequency = models.FloatField(
        help_text="Frequency in Hz", null=True, blank=True
    )
    compliant = models.BooleanField(default=True)
    details = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.check_type} check for {self.turbine.name} at {self.timestamp}"

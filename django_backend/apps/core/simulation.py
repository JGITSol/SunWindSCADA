"""
SCADA Simulation Engine - Core simulation components for wind power integration.
"""
import numpy as np
import pandas as pd
import jax.numpy as jnp
from jax import jit
import time
import json
import logging
from datetime import datetime, timedelta
import threading
import asyncio
from django.utils import timezone
from .models import WindTurbine, WeatherData, TurbineMeasurement, Scenario, GridComplianceCheck

logger = logging.getLogger(__name__)

class WindTurbineSimulator:
    """
    Digital twin simulator for wind turbines.
    Uses windpowerlib models and JAX acceleration.
    """
    def __init__(self, turbine_model=None):
        self.turbine_model = turbine_model
        self._setup_power_curve()
        
    def _setup_power_curve(self):
        """Set up a typical power curve for a wind turbine"""
        # Wind speeds in m/s
        self.wind_speeds = jnp.array([0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 25])
        
        # Power output in W (for a 3.05 MW turbine)
        if self.turbine_model and hasattr(self.turbine_model, 'nominal_power'):
            max_power = self.turbine_model.nominal_power
        else:
            max_power = 3.05e6  # Default to 3.05 MW
            
        self.power_values = jnp.array([
            0, 0, 
            max_power * 0.03, max_power * 0.08, max_power * 0.15, 
            max_power * 0.23, max_power * 0.33, max_power * 0.44, 
            max_power * 0.56, max_power * 0.67, max_power * 0.77, 
            max_power * 0.87, max_power * 0.93, max_power * 0.97, 
            max_power * 0.98, max_power, max_power
        ])
    
    @jit
    def _calculate_power(self, wind_speed):
        """JAX-accelerated power calculation from wind speed"""
        return jnp.interp(wind_speed, self.wind_speeds, self.power_values)
    
    def calculate_power_output(self, wind_speed, turbine_status='operational'):
        """
        Calculate power output based on wind speed and turbine status
        
        Args:
            wind_speed: Wind speed in m/s
            turbine_status: Current turbine status
            
        Returns:
            Power output in W
        """
        if turbine_status != 'operational':
            return 0.0
            
        # Apply small random variations to simulate real-world conditions
        wind_speed_adjusted = wind_speed * (1 + np.random.normal(0, 0.05))
        
        # Calculate power using JAX-accelerated function
        power = float(self._calculate_power(wind_speed_adjusted))
        
        # Apply efficiency factor (random small variations)
        efficiency = 0.95 + np.random.normal(0, 0.03)
        power *= max(0.85, min(1.0, efficiency))
        
        return power
        
    def calculate_rotor_speed(self, wind_speed, turbine_status='operational'):
        """Calculate rotor speed in RPM based on wind speed"""
        if turbine_status != 'operational':
            return 0.0
            
        # Simple model: rotor speed increases with wind speed up to rated speed
        if wind_speed < 3.0:
            return 0.0
        elif wind_speed < 12.0:
            return 5.0 + (wind_speed - 3.0) * 1.2
        else:
            return 15.0  # Maximum RPM
            
    def calculate_blade_pitch(self, wind_speed, turbine_status='operational'):
        """Calculate blade pitch angle in degrees based on wind speed"""
        if turbine_status != 'operational':
            return 0.0
            
        # Simple model: pitch increases above rated wind speed to limit power
        if wind_speed < 12.0:
            return 0.0  # No pitch below rated wind speed
        else:
            return min(45.0, (wind_speed - 12.0) * 5.0)  # Increase pitch with wind speed

class GridComplianceSimulator:
    """
    Simulator for grid compliance checks (LVRT/HVRT, frequency, etc.)
    Uses JAX for performance.
    """
    def __init__(self):
        # LVRT curve points (voltage in p.u., duration in seconds)
        self.lvrt_curve_x = jnp.array([0.0, 0.3, 0.7, 0.85, 0.9])
        self.lvrt_curve_y = jnp.array([0.15, 0.15, 0.7, 1.5, 3.0])
        
        # HVRT curve points
        self.hvrt_curve_x = jnp.array([1.1, 1.15, 1.2])
        self.hvrt_curve_y = jnp.array([60.0, 1.0, 0.1])
    
    @jit
    def check_lvrt(self, voltage_pu, duration):
        """
        Check if voltage/duration point complies with LVRT curve
        
        Args:
            voltage_pu: Voltage in per-unit (p.u.)
            duration: Event duration in seconds
            
        Returns:
            True if compliant, False otherwise
        """
        max_allowed_duration = jnp.interp(voltage_pu, self.lvrt_curve_x, self.lvrt_curve_y)
        return duration <= max_allowed_duration
    
    @jit
    def check_hvrt(self, voltage_pu, duration):
        """
        Check if voltage/duration point complies with HVRT curve
        
        Args:
            voltage_pu: Voltage in per-unit (p.u.)
            duration: Event duration in seconds
            
        Returns:
            True if compliant, False otherwise
        """
        max_allowed_duration = jnp.interp(voltage_pu, self.hvrt_curve_x, self.hvrt_curve_y)
        return duration <= max_allowed_duration
    
    @jit
    def calculate_reactive_power(self, voltage_deviation):
        """
        Calculate required reactive power compensation
        
        Args:
            voltage_deviation: Deviation from nominal voltage (p.u.)
            
        Returns:
            Required reactive power in p.u.
        """
        # Simple model: provide reactive power proportional to voltage deviation
        return 2.0 * voltage_deviation

class ScenarioManager:
    """
    Manager for running different simulation scenarios
    """
    def __init__(self):
        self.turbine_simulators = {}
        self.grid_simulator = GridComplianceSimulator()
        self.active_scenario = None
        self.running = False
        self.thread = None
        
    def initialize_turbines(self):
        """Initialize simulators for all turbines in the database"""
        turbines = WindTurbine.objects.all()
        for turbine in turbines:
            self.turbine_simulators[turbine.id] = WindTurbineSimulator(turbine)
    
    def get_active_scenario(self):
        """Get the currently active scenario from the database"""
        try:
            return Scenario.objects.filter(active=True).first()
        except Exception as e:
            logger.error(f"Error getting active scenario: {e}")
            return None
    
    def generate_weather_data(self, scenario=None):
        """
        Generate simulated weather data based on the active scenario
        
        Args:
            scenario: Optional scenario object, otherwise uses active scenario
            
        Returns:
            Dictionary with weather data
        """
        if scenario is None:
            scenario = self.get_active_scenario()
        
        # Base weather parameters
        base_wind_speed = 8.0
        base_temperature = 15.0
        base_pressure = 1013.0
        base_humidity = 70.0
        
        # Adjust based on scenario type
        if scenario and scenario.scenario_type:
            if scenario.scenario_type == 'storm':
                base_wind_speed = 20.0 + np.random.normal(0, 2.0)
                base_pressure = 990.0 + np.random.normal(0, 5.0)
                base_humidity = 85.0 + np.random.normal(0, 5.0)
            elif scenario.scenario_type == 'normal_operation':
                base_wind_speed = 8.0 + np.random.normal(0, 1.5)
            
            # Apply custom parameters if available
            if scenario.parameters:
                params = scenario.parameters
                if 'wind_speed' in params:
                    base_wind_speed = float(params['wind_speed'])
                if 'temperature' in params:
                    base_temperature = float(params['temperature'])
        
        # Add random variations
        wind_speed = max(0, base_wind_speed + np.random.normal(0, 0.8))
        wind_direction = np.random.uniform(0, 360)
        temperature = base_temperature + np.random.normal(0, 1.0)
        pressure = base_pressure + np.random.normal(0, 2.0)
        humidity = min(100, max(0, base_humidity + np.random.normal(0, 3.0)))
        
        return {
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'temperature': temperature,
            'pressure': pressure,
            'humidity': humidity
        }
    
    def generate_grid_event(self, scenario=None):
        """
        Generate a grid event based on the active scenario
        
        Args:
            scenario: Optional scenario object, otherwise uses active scenario
            
        Returns:
            Dictionary with grid event data or None if no event
        """
        if scenario is None:
            scenario = self.get_active_scenario()
            
        if not scenario:
            return None
            
        # Default: no grid event
        grid_event = None
        
        # Generate grid event based on scenario type
        if scenario.scenario_type == 'grid_fault':
            # Get parameters from scenario or use defaults
            params = scenario.parameters or {}
            voltage = params.get('voltage', 0.7)
            duration = params.get('duration', 0.2)
            
            grid_event = {
                'type': 'voltage_dip',
                'voltage': float(voltage),
                'duration': float(duration)
            }
        
        return grid_event
    
    def run_simulation_step(self):
        """
        Run a single simulation step:
        1. Generate weather data
        2. Calculate turbine outputs
        3. Check grid compliance
        4. Store results in database
        """
        try:
            # Get active scenario
            scenario = self.get_active_scenario()
            
            # Generate weather data
            weather_data = self.generate_weather_data(scenario)
            
            # Save weather data to database
            db_weather = WeatherData.objects.create(
                wind_speed=weather_data['wind_speed'],
                wind_direction=weather_data['wind_direction'],
                temperature=weather_data['temperature'],
                pressure=weather_data['pressure'],
                humidity=weather_data['humidity']
            )
            
            # Generate potential grid event
            grid_event = self.generate_grid_event(scenario)
            
            # Process each turbine
            for turbine_id, simulator in self.turbine_simulators.items():
                try:
                    turbine = WindTurbine.objects.get(id=turbine_id)
                    
                    # Calculate power output and other parameters
                    power_output = simulator.calculate_power_output(
                        weather_data['wind_speed'], 
                        turbine.status
                    )
                    
                    rotor_speed = simulator.calculate_rotor_speed(
                        weather_data['wind_speed'],
                        turbine.status
                    )
                    
                    blade_pitch = simulator.calculate_blade_pitch(
                        weather_data['wind_speed'],
                        turbine.status
                    )
                    
                    # Default grid parameters
                    grid_voltage = 1.0
                    grid_frequency = 50.0
                    
                    # Apply grid event if present
                    if grid_event and grid_event['type'] == 'voltage_dip':
                        grid_voltage = grid_event['voltage']
                        
                        # Check LVRT compliance
                        compliant = self.grid_simulator.check_lvrt(
                            grid_voltage, 
                            grid_event['duration']
                        )
                        
                        # Record compliance check
                        GridComplianceCheck.objects.create(
                            turbine=turbine,
                            check_type='lvrt',
                            voltage_pu=grid_voltage,
                            duration=grid_event['duration'],
                            compliant=compliant,
                            details={
                                'event_type': 'voltage_dip',
                                'max_allowed_duration': float(jnp.interp(
                                    grid_voltage, 
                                    self.grid_simulator.lvrt_curve_x,
                                    self.grid_simulator.lvrt_curve_y
                                ))
                            }
                        )
                    
                    # Save turbine measurement
                    TurbineMeasurement.objects.create(
                        turbine=turbine,
                        power_output=power_output,
                        wind_speed=weather_data['wind_speed'],
                        rotor_speed=rotor_speed,
                        blade_pitch=blade_pitch,
                        nacelle_orientation=weather_data['wind_direction'],
                        grid_voltage=grid_voltage * 400.0,  # Convert p.u. to V
                        grid_frequency=grid_frequency
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing turbine {turbine_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in simulation step: {e}")
    
    def start_simulation(self):
        """Start the simulation in a background thread"""
        if self.running:
            return
            
        self.running = True
        self.initialize_turbines()
        self.thread = threading.Thread(target=self._simulation_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            
    def _simulation_loop(self):
        """Main simulation loop running in background thread"""
        while self.running:
            self.run_simulation_step()
            time.sleep(5.0)  # Run every 5 seconds

# Singleton instance
scenario_manager = ScenarioManager()

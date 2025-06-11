"""
Asynchronous tasks for SCADA simulation.
Implements Celery tasks for background processing of simulation scenarios.
"""
import logging
import time
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import WindTurbine, WeatherData, TurbineMeasurement, Scenario, GridComplianceCheck
from .simulation import scenario_manager
from .visualization import visualizer

logger = logging.getLogger(__name__)

@shared_task
def run_simulation_cycle():
    """
    Run a complete simulation cycle:
    1. Execute simulation step
    2. Update visualizations
    """
    try:
        # Run simulation step
        scenario_manager.run_simulation_step()
        return {"status": "success", "timestamp": timezone.now().isoformat()}
    except Exception as e:
        logger.error(f"Error in simulation cycle: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def start_simulation():
    """Start the simulation engine"""
    try:
        scenario_manager.start_simulation()
        visualizer.start_data_collection()
        return {"status": "success", "message": "Simulation started"}
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def stop_simulation():
    """Stop the simulation engine"""
    try:
        scenario_manager.stop_simulation()
        visualizer.stop_data_collection()
        return {"status": "success", "message": "Simulation stopped"}
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def activate_scenario(scenario_id):
    """
    Activate a specific scenario
    
    Args:
        scenario_id: ID of the scenario to activate
    """
    try:
        # Deactivate all scenarios
        Scenario.objects.all().update(active=False)
        
        # Activate the specified scenario
        scenario = Scenario.objects.get(id=scenario_id)
        scenario.active = True
        scenario.save()
        
        return {
            "status": "success", 
            "message": f"Scenario '{scenario.name}' activated"
        }
    except Scenario.DoesNotExist:
        return {"status": "error", "error": f"Scenario with ID {scenario_id} not found"}
    except Exception as e:
        logger.error(f"Error activating scenario: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def cleanup_old_data(days=7):
    """
    Clean up old measurement data to prevent database bloat
    
    Args:
        days: Number of days of data to keep
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old measurements
        deleted_measurements = TurbineMeasurement.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        # Delete old weather data
        deleted_weather = WeatherData.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        # Delete old compliance checks
        deleted_checks = GridComplianceCheck.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        return {
            "status": "success",
            "deleted": {
                "measurements": deleted_measurements[0],
                "weather": deleted_weather[0],
                "compliance_checks": deleted_checks[0]
            }
        }
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        return {"status": "error", "error": str(e)}

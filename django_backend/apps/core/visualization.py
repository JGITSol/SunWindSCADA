"""
Real-time visualization components for SCADA data.
Implements optimized matplotlib/plotly visualizations with thread-safe data handling.
"""

import base64
import io
import logging
import threading
import time
from collections import deque

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from .models import TurbineMeasurement, WeatherData, WindTurbine

logger = logging.getLogger(__name__)


class ScadaVisualizer:
    """
    Thread-safe, high-performance visualization for SCADA data.
    Uses circular buffers and optimized rendering for real-time updates.
    """

    def __init__(self, max_points=500, refresh_rate=30):
        # Circular buffers for efficient data handling
        self.time_buffer = deque(maxlen=max_points)
        self.data_buffers = {}

        # Thread-safe data queue
        self.data_queue = deque(maxlen=2000)
        self.lock = threading.Lock()

        # Visualization parameters
        self.refresh_rate = refresh_rate
        self.max_points = max_points
        self.running = False
        self.thread = None

    def initialize_buffers(self, data_keys):
        """Initialize data buffers for specified keys"""
        with self.lock:
            for key in data_keys:
                if key not in self.data_buffers:
                    self.data_buffers[key] = deque(maxlen=self.max_points)

    def add_data_point(self, timestamp, data_dict):
        """
        Add a data point to the queue

        Args:
            timestamp: Timestamp for the data point
            data_dict: Dictionary of {key: value} pairs
        """
        with self.lock:
            self.data_queue.append((timestamp, data_dict))

    def update_buffers(self):
        """Update internal buffers from the data queue"""
        with self.lock:
            while self.data_queue:
                timestamp, data_dict = self.data_queue.popleft()

                self.time_buffer.append(timestamp)

                # Initialize buffers for any new keys
                self.initialize_buffers(data_dict.keys())

                # Update each data buffer
                for key, value in data_dict.items():
                    self.data_buffers[key].append(value)

    def generate_power_plot(self, width=10, height=6, dpi=100):
        """
        Generate a power output plot for all turbines

        Returns:
            Base64-encoded PNG image
        """
        # Create figure and axes
        fig = Figure(figsize=(width, height), dpi=dpi)
        ax = fig.add_subplot(1, 1, 1)

        # Update buffers
        self.update_buffers()

        # Get turbine names for legend
        turbines = WindTurbine.objects.all()
        turbine_names = {t.id: t.name for t in turbines}

        # Plot each turbine's power output
        with self.lock:
            x_data = list(self.time_buffer)

            for turbine_id, name in turbine_names.items():
                key = f"power_{turbine_id}"
                if key in self.data_buffers and len(self.data_buffers[key]) > 0:
                    y_data = list(self.data_buffers[key])
                    if len(y_data) == len(x_data):
                        ax.plot(x_data, y_data, label=name)

        # Configure plot
        ax.set_title("Wind Turbine Power Output")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (W)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right")

        # Format x-axis as time
        fig.autofmt_xdate()

        # Render to PNG
        canvas = FigureCanvasAgg(fig)
        buf = io.BytesIO()
        canvas.print_png(buf)

        # Convert to base64
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        return f"data:image/png;base64,{data}"

    def generate_wind_plot(self, width=10, height=6, dpi=100):
        """
        Generate a wind speed plot

        Returns:
            Base64-encoded PNG image
        """
        # Create figure and axes
        fig = Figure(figsize=(width, height), dpi=dpi)
        ax = fig.add_subplot(1, 1, 1)

        # Update buffers
        self.update_buffers()

        # Plot wind speed
        with self.lock:
            x_data = list(self.time_buffer)

            if (
                "wind_speed" in self.data_buffers
                and len(self.data_buffers["wind_speed"]) > 0
            ):
                y_data = list(self.data_buffers["wind_speed"])
                if len(y_data) == len(x_data):
                    ax.plot(x_data, y_data, label="Wind Speed", color="blue")

        # Configure plot
        ax.set_title("Wind Speed")
        ax.set_xlabel("Time")
        ax.set_ylabel("Wind Speed (m/s)")
        ax.grid(True, alpha=0.3)

        # Format x-axis as time
        fig.autofmt_xdate()

        # Render to PNG
        canvas = FigureCanvasAgg(fig)
        buf = io.BytesIO()
        canvas.print_png(buf)

        # Convert to base64
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        return f"data:image/png;base64,{data}"

    def start_data_collection(self):
        """Start collecting data in a background thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._data_collection_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop_data_collection(self):
        """Stop data collection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def _data_collection_loop(self):
        """Background thread for data collection"""
        while self.running:
            try:
                # Get latest weather data
                latest_weather = WeatherData.objects.order_by("-timestamp").first()

                if latest_weather:
                    self.add_data_point(
                        latest_weather.timestamp,
                        {
                            "wind_speed": latest_weather.wind_speed,
                            "temperature": latest_weather.temperature,
                            "pressure": latest_weather.pressure,
                            "humidity": latest_weather.humidity,
                        },
                    )

                # Get latest turbine measurements
                turbines = WindTurbine.objects.all()

                for turbine in turbines:
                    latest_measurement = (
                        TurbineMeasurement.objects.filter(turbine=turbine)
                        .order_by("-timestamp")
                        .first()
                    )

                    if latest_measurement:
                        self.add_data_point(
                            latest_measurement.timestamp,
                            {
                                f"power_{turbine.id}": latest_measurement.power_output,
                                f"rotor_speed_{turbine.id}": latest_measurement.rotor_speed,
                                f"blade_pitch_{turbine.id}": latest_measurement.blade_pitch,
                            },
                        )

            except Exception as e:
                logger.error(f"Error in data collection: {e}")

            time.sleep(1.0)  # Collect data every second


# Singleton instance
visualizer = ScadaVisualizer()

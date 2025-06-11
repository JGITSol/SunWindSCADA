"""
SunWindSCADA - Real-time SCADA Dashboard for Wind Power Integration
Built with Reflex for real-time reactivity and Django backend integration
"""
import reflex as rx
import asyncio
import httpx
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# API Configuration
import os
API_BASE_URL = os.getenv("REFLEX_API_URL", os.getenv("API_URL", "http://localhost:8000/api"))

# State definition for the dashboard
class DashboardState(rx.State):
    """State for the SCADA dashboard."""
    
    # Turbine data
    turbines: list = []
    selected_turbine_id: int | None = None
    
    # Measurement data
    measurements: list = []
    weather_data: list = []
    
    # Scenarios
    scenarios: list = []
    active_scenario: int | None = None
    
    # UI state
    is_loading: bool = False
    error_message: str = ""
    refresh_interval: int = 5  # seconds
    chart_timespan: str = "1h"  # 1h, 6h, 24h

    def set_refresh_interval(self, interval: str):
        """Set the refresh interval for data fetching."""
        # Convert string like '5s', '15s', '1m' to integer seconds
        if interval.endswith('s'):
            self.refresh_interval = int(interval[:-1])
        elif interval.endswith('m'):
            self.refresh_interval = int(interval[:-1]) * 60
        else:
            # Default fallback
            self.refresh_interval = 5
    
    def set_error(self, message: str):
        """Set an error message."""
        self.error_message = message
    
    def clear_error(self):
        """Clear the error message."""
        self.error_message = ""
    
    def set_selected_turbine(self, turbine_id: int):
        """Set the selected turbine."""
        self.selected_turbine_id = turbine_id
        return self.fetch_turbine_measurements

    async def fetch_turbines(self):
        """Fetch all wind turbines from the API."""
        self.is_loading = True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/wind-turbines/")
                response.raise_for_status()
                self.turbines = response.json()
                if self.turbines and not self.selected_turbine_id:
                    self.selected_turbine_id = self.turbines[0]['id']
        except Exception as e:
            self.set_error(f"Failed to fetch turbines: {str(e)}")
        finally:
            self.is_loading = False

    async def fetch_turbine_measurements(self):
        """Fetch measurements for the selected turbine."""
        if not self.selected_turbine_id:
            return
            
        self.is_loading = True
        try:
            # Calculate time range based on selected timespan
            end_time = datetime.utcnow()
            if self.chart_timespan == "1h":
                start_time = end_time - timedelta(hours=1)
            elif self.chart_timespan == "6h":
                start_time = end_time - timedelta(hours=6)
            else:  # 24h
                start_time = end_time - timedelta(days=1)
                
            params = {
                "turbine_id": self.selected_turbine_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/turbine-measurements/",
                    params=params
                )
                response.raise_for_status()
                self.measurements = response.json()
                
                # Also fetch weather data for the same time period
                weather_response = await client.get(
                    f"{API_BASE_URL}/weather-data/",
                    params={
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat()
                    }
                )
                weather_response.raise_for_status()
                self.weather_data = weather_response.json()
        except Exception as e:
            self.set_error(f"Failed to fetch measurements: {str(e)}")
        finally:
            self.is_loading = False

    # Helper functions for creating charts
    @staticmethod
    def create_power_chart(measurements):
        """Create a power output chart using Plotly."""
        # For non-reactive contexts
        if not isinstance(measurements, rx.Var):
            # Create an empty chart if no measurements
            if not measurements:
                return go.Figure().update_layout(title="No data available")
            
            # Create chart with data
            df = pd.DataFrame(measurements)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df.get('power_output', 0),
                mode='lines+markers',
                name='Power Output (kW)',
                line=dict(color='#4CAF50')
            ))
            fig.update_layout(
                title='Power Output Over Time',
                xaxis_title='Time',
                yaxis_title='Power (kW)',
                template='plotly_white',
                margin=dict(l=50, r=50, t=50, b=50),
                height=300
            )
            return fig
        
        # For reactive contexts, always return a valid figure
        # The data will be processed client-side by Reflex
        fig = go.Figure()
        fig.update_layout(
            title='Power Output Over Time',
            xaxis_title='Time',
            yaxis_title='Power (kW)',
            template='plotly_white',
            margin=dict(l=50, r=50, t=50, b=50),
            height=300
        )
        return fig

    @staticmethod
    def create_wind_speed_chart(measurements):
        """Create a wind speed chart using Plotly."""
        # For non-reactive contexts
        if not isinstance(measurements, rx.Var):
            # Create an empty chart if no measurements
            if not measurements:
                return go.Figure().update_layout(title="No data available")
            
            # Create chart with data
            df = pd.DataFrame(measurements)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df.get('wind_speed', 0),
                mode='lines+markers',
                name='Wind Speed (m/s)',
                line=dict(color='#2196F3')
            ))
            fig.update_layout(
                title='Wind Speed Over Time',
                xaxis_title='Time',
                yaxis_title='Wind Speed (m/s)',
                template='plotly_white',
                margin=dict(l=50, r=50, t=50, b=50),
                height=300
            )
            return fig
        
        # For reactive contexts, always return a valid figure
        # The data will be processed client-side by Reflex
        fig = go.Figure()
        fig.update_layout(
            title='Wind Speed Over Time',
            xaxis_title='Time',
            yaxis_title='Wind Speed (m/s)',
            template='plotly_white',
            margin=dict(l=50, r=50, t=50, b=50),
            height=300
        )
        return fig

    @staticmethod
    def create_turbine_status_chart(turbines):
        """Create a turbine status chart using Plotly."""
        # For non-reactive contexts
        if not isinstance(turbines, rx.Var):
            # Create an empty chart if no turbines
            if not turbines:
                return go.Figure().update_layout(title="No data available")
            
            # Create chart with data
            df = pd.DataFrame(turbines)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['status'] = df.get('status', 1)  # Default to running
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['status'],
                mode='lines+markers',
                name='Status',
                line=dict(color='#9C27B0')
            ))
            status_map = {0: 'Stopped', 1: 'Running', 2: 'Warning', 3: 'Error'}
            fig.update_layout(
                title='Turbine Status',
                xaxis_title='Time',
                yaxis=dict(
                    title='Status',
                    tickmode='array',
                    tickvals=list(status_map.keys()),
                    ticktext=list(status_map.values())
                ),
                template='plotly_white',
                margin=dict(l=50, r=50, t=50, b=50),
                height=300
            )
            return fig
        
        # For reactive contexts, always return a valid figure
        # The data will be processed client-side by Reflex
        status_map = {0: 'Stopped', 1: 'Running', 2: 'Warning', 3: 'Error'}
        fig = go.Figure()
        fig.update_layout(
            title='Turbine Status',
            xaxis_title='Time',
            yaxis=dict(
                title='Status',
                tickmode='array',
                tickvals=list(status_map.keys()),
                ticktext=list(status_map.values())
            ),
            template='plotly_white',
            margin=dict(l=50, r=50, t=50, b=50),
            height=300
        )
        return fig

# UI Components
def navbar():
    """Create the navigation bar."""
    return rx.box(
        rx.hstack(
            rx.heading("SunWindSCADA", size="7"),
            rx.spacer(),
            rx.hstack(
                rx.text("Refresh Interval:"),
                rx.select(
                    ["5s", "15s", "30s", "1m", "5m"],
                    value="5s",
                    on_change=DashboardState.set_refresh_interval,
                ),
            ),
        ),
        padding="1rem",
        border_bottom="1px solid #eaeaea",
    )

def sidebar():
    """Create the sidebar with turbine selection and scenarios."""
    return rx.box(
        rx.vstack(
            rx.heading("Turbines", size="5"),
            rx.vstack(
                rx.foreach(
                    DashboardState.turbines.to(list[dict]),
                    lambda turbine: rx.button(
                        f"Turbine {turbine.id} - {turbine.get('name', 'Unnamed')}",
                        on_click=lambda: DashboardState.set_selected_turbine(turbine.id),
                        is_active=DashboardState.selected_turbine_id == turbine.id,
                        width="100%",
                        variant="ghost",
                    ),
                ),
                align_items="stretch",
                width="100%",
            ),
            rx.divider(),
            rx.heading("Scenarios", size="5"),
            rx.vstack(
                rx.foreach(
                    DashboardState.scenarios.to(list[dict]),
                    lambda scenario: rx.button(
                        scenario.name,
                        # Add scenario selection logic here
                        width="100%",
                        variant="ghost",
                    ),
                ),
                align_items="stretch",
                width="100%",
            ),
        ),
        padding="1rem",
        border_right="1px solid #eaeaea",
        min_width="220px",
        max_width="260px",
        height="100vh",
        position="fixed",
        left=0,
        top=0,
        bg="#FAFAFA",
    )

def main_content():
    """Create the main content area with charts and status."""
    return rx.container(
        rx.vstack(
            rx.heading("Dashboard", size="5"),
            rx.divider(),
            rx.container(
                rx.text("Power Output", font_weight="bold"),
                rx.plotly(data=DashboardState.create_power_chart([])),
                padding="1rem",
                border="1px solid #eaeaea",
                border_radius="md",
                margin_bottom="2rem",
                background="white",
            ),
            rx.container(
                rx.text("Wind Speed", font_weight="bold"),
                rx.plotly(data=DashboardState.create_wind_speed_chart([])),
                padding="1rem",
                border="1px solid #eaeaea",
                border_radius="md",
                margin_bottom="2rem",
                background="white",
            ),
            rx.container(
                rx.text("Turbine Status", font_weight="bold"),
                rx.plotly(data=DashboardState.create_turbine_status_chart([])),
                padding="1rem",
                border="1px solid #eaeaea",
                border_radius="md",
                margin_bottom="2rem",
                background="white",
            ),
        ),
        margin_left="260px",
        padding="2rem",
        min_height="100vh",
        width="calc(100% - 260px)",
        max_width="calc(100% - 260px)",
        background="#f5f5f5",
    )

def error_alert():
    """Display error messages."""
    return rx.cond(
        DashboardState.error_message != "",
        rx.box(
            rx.text(DashboardState.error_message, color="red"),
            rx.button("Close", on_click=DashboardState.clear_error),
            padding="1em",
            border="1px solid red",
            border_radius="md",
            background_color="rgba(255, 0, 0, 0.1)",
        ),
        None,
    )

def index():
    """The main app layout."""
    return rx.container(
        navbar(),
        rx.hstack(
            sidebar(),
            main_content(),
            align_items="flex-start",
            width="100%",
        ),
        error_alert(),
        width="100%",
        max_width="100%",
        padding="0",
        margin="0",
    )

app = rx.App()
app.add_page(index, title="SunWindSCADA Dashboard")

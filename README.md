# SunWindSCADA: SCADA Simulation with Wind Power Integration

A comprehensive, modular SCADA simulation platform for wind farm operations, grid compliance, and real-time visualization. Combines a Django 5 backend, Reflex (Pynecone) real-time frontend, and advanced simulation/ML libraries.

## Features
- Wind turbine digital twin (windpowerlib + LSTM)
- Grid compliance (LVRT/HVRT, JAX acceleration)
- Async Modbus, OPC UA, MQTT (TLS)
- Real-time dashboard (Reflex + Plotly/Matplotlib)
- Scenario orchestration (normal, grid fault, turbine failure)
- PostgreSQL database, secure secrets, Polish 2025 energy compliance

## Project Structure
```
SunWindSCADA/
├── django_backend/
│   ├── config/
│   ├── apps/core/
│   └── manage.py
├── reflex_frontend/
├── requirements.txt
├── README.md
├── .env.example
```

## Quickstart
1. Clone repo & install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set secrets/DB.
3. Initialize DB:
   ```bash
   cd django_backend
   python manage.py migrate
   ```
4. Start backend (ASGI):
   ```bash
   uvicorn config.asgi:application --reload
   ```
5. Start Reflex frontend:
   ```bash
   cd reflex_frontend
   reflex run
   ```
6. Access dashboard at http://localhost:3000

## Architecture
- **Django 5**: Backend API, simulation orchestration, PostgreSQL
- **Reflex**: Real-time, interactive dashboard (WebSocket/REST)
- **Celery/Redis**: Async simulation tasks
- **windpowerlib, JAX, TensorFlow**: Simulation, ML, compliance

## Main Components
- `django_backend/apps/core/models.py`: Turbine, Weather, Scenario, Measurement, etc.
- `django_backend/apps/core/views.py`: API endpoints for real-time data
- `django_backend/apps/core/tasks.py`: Async simulation workers
- `reflex_frontend/reflex_frontend.py`: Dashboard UI, real-time charts

## Security & Compliance
- TLS for MQTT, .env for secrets, Polish energy code compliance

## References
- windpowerlib: https://github.com/wind-python/windpowerlib
- Reflex: https://reflex.dev
- Django: https://www.djangoproject.com/

---

For detailed API and customization, see each module's docstring or open an issue.

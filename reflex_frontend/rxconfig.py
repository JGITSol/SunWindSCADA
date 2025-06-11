import os
import reflex as rx
from dotenv import load_dotenv

load_dotenv()

config = rx.Config(
    app_name="reflex_frontend",
    db_url=os.getenv("REFLEX_DB_URL", os.getenv("DB_URL", "postgresql://scada_user:scada_password@db:5432/scada_db")),
    api_url=os.getenv("REFLEX_API_URL", os.getenv("API_URL", "http://django:8000/api")),
    env=os.getenv("REFLEX_ENV", "dev"),
    frontend_port=3000,
    backend_port=8000,
    telemetry_enabled=False,
    app_module_import="reflex_frontend.app",
    tailwind={
        "plugins": ["@tailwindcss/typography"],
    },
    # Docker-specific settings
    backend_host="0.0.0.0",  # Bind to all interfaces
    frontend_host="0.0.0.0", # Bind to all interfaces
)

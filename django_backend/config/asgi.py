import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.config.settings")

# Initialize Django ASGI app
django_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter

application = ProtocolTypeRouter({
    "http": django_app,
    # WebSocket routing can be added here later for the Dash frontend.
})


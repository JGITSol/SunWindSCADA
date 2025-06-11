import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.config.settings')

# Initialize Django ASGI app
django_app = get_asgi_application()

# Optionally: integrate Reflex ASGI app here
# from reflex_frontend.rxconfig import config as reflex_config
# reflex_app = Reflex(config=reflex_config)
# application = ProtocolTypeRouter({
#     "http": django_app,
#     "websocket": AuthMiddlewareStack(
#         URLRouter([
#             # Add websocket routes here
#         ])
#     ),
# })

application = django_app

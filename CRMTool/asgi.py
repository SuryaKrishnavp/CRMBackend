import os
import django  # <-- Add this

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import leads_section.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "devlok_crm.settings")
django.setup()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(  
            URLRouter(
                leads_section.routing.websocket_urlpatterns 
            )
        ),
    }
)

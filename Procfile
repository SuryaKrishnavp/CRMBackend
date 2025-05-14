web: daphne -b 0.0.0.0 -p 8000 CRMTool.asgi:application
worker: celery -A CRMTool worker --loglevel=info

import os
from django.core.wsgi import get_wsgi_application

# SHU QATORNI QO'SHING (bo'lmasa xato beradi)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
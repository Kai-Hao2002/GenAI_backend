"""
WSGI config for GENAI_BACKEND project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GENAI_BACKEND.settings')

application = get_wsgi_application()

from django.core.management import call_command
import traceback

try:
    call_command('migrate', interactive=False)
    print("✅ Migration succeeded")
except Exception as e:
    print("❌ Migration failed:")
    traceback.print_exc()



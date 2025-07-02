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

def run_startup_tasks():
    import threading
    import sys
    from django.core.management import call_command
    from django.contrib.auth import get_user_model

    def task():
        try:
            call_command('migrate', interactive=False)
        except Exception as e:
            print(f"Error during migrate: {e}", file=sys.stderr)

        
        User = get_user_model()
        from django.conf import settings
        import os

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if username and email and password:
            try:
                if not User.objects.filter(username=username).exists():
                    User.objects.create_superuser(username=username, email=email, password=password)
                    print(f"Superuser '{username}' created.")
                else:
                    print(f"Superuser '{username}' already exists.")
            except Exception as e:
                print(f"Error creating superuser: {e}", file=sys.stderr)
        else:
            print("Superuser environment variables not set, skipping superuser creation.")

    threading.Thread(target=task, daemon=True).start()

run_startup_tasks()




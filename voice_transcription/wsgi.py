"""
WSGI config for voice_transcription project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from whitenoise import WhiteNoise
from django.core.wsgi import get_wsgi_application

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "voice_transcription.settings")

# Initialize the WSGI application
application = get_wsgi_application()

# Wrap the application with WhiteNoise to serve static files
application = WhiteNoise(application, root=os.path.join(os.path.dirname(__file__), 'staticfiles'))

# Add additional static files if needed

# Alias for the WSGI application
app = application

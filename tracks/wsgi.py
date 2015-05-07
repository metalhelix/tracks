"""
WSGI config for tracks project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) ## i.e. sys.path.append('/microarray/tracks/')
#os.environ.setdefault("PRODUCTION", "1") # PRODUCTION is best set in calling environment, i.e. in service configuration for uwsgi
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracks.settings")
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracks.settings.production")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

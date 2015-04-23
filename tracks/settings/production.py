from .base import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tracks',
        'USER': 'deployer',
        'PASSWORD': 'ghxPyucj',
        'HOST': '',  # Set to empty string for localhost.
        'PORT': '',  # Set to empty string for default.
        'CONN_MAX_AGE': 600,  # number of seconds database connections should persist for
    }
}

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.stowers.org']

try:
	from .local import *
except ImportError:
	pass

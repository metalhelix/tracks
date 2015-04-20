import os
if os.environ.get('PRODUCTION', None):
    from .production import *
else:
    from .dev import *

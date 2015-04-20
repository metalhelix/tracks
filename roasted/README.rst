=====
Roasted
=====

Roasted is a simple Django app for URL shortening by a user determined keyword or auto-suggested.  

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "roasted" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'roasted',
    )

2. Include the roasted URLconf in your project urls.py like this::

    url(r'^/', include('roasted.urls')),

3. Run `python manage.py migrate` to create the roasted models.

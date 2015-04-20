from django.conf.urls import patterns, include, url
from django.contrib import admin

import settings

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tracks.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^contact/', include('contact_form.urls')),
    url(r'', include('roasted.urls'))
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

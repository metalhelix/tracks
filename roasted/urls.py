from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView
from tastypie.api import Api

from roasted.api import TargetSearch

rest_api = Api(api_name='v1')
rest_api.register(TargetSearch())


urlpatterns = patterns('',)

#urlpatterns += patterns('',
#    (r'^$',              TemplateView.as_view(template_name='index.html')),
#    (r'^robots.txt$',    TemplateView.as_view(template_name='robots.txt')),
#)

urlpatterns += patterns('roasted.views',

    url(r'^redirect/add_redirect/$', 'add_redirect', name='roasted-add_redirect'),
    #url(r'^redirect/add_redirect/results.html', TemplateView.as_view(template_name='roasted/results.html')),
    url(r'^redirect/all/$', 'all_redirect', name='roasted-redirect_index'),

    url(r'api/', include(rest_api.urls)),

    url(r'^(?P<key>[a-zA-Z0-9_]{1,10})[\,\)]*[\./]', 'redirect', name='roasted-redirect'),
    url(r'$', 'tracks_home', name='roasted-tracks_home'),
)

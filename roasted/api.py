from tastypie.resources import ModelResource

from .models import Target

class TargetSearch(ModelResource):
    class Meta:
        resource_name = 'ajaxsearch'
        allowed_methods = ['get','post']

    def get_list(self, request, **kwargs):
        prefix = request.GET.get('q')
        if prefix:
            targets = list(Targets.objects.filter(key__startswith=prefix)).values(key)
            return self.create_response(request, {'targets', targets})
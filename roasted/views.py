from django.http import HttpResponse, HttpResponseNotFound
from django.http import HttpResponsePermanentRedirect
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from .models import Target
from .forms import TargetForm

class HttpResponseSneak(HttpResponse):
    status_code = 200

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = redirect_to

def redirect(request, key):
    target = get_object_or_404(Target, key=key)

    try:
        hit = RedirectHit()
        hit.target = target
        hit.referer = request.META.get("HTTP_REFERER", "")
        hit.remote_host = request.META.get("REMOTE_ADDR", "")
        hit.remote_host = request.META.get("HTTP_X_FORWARDED_FOR", hit.remote_host)
        hit.save()
    except:
        # TODO: fix silent error
        pass

    return HttpResponsePermanentRedirect(target.target_url)

def add_redirect(request):
    if request.method == 'POST':
        form = TargetForm(request.POST)
        if form.is_valid():
            instance = form.save()
            key = instance.key
            #return render(request, 'roasted/results.html',{'key':key})
            return HttpResponseRedirect(reverse('roasted-redirect_index'))
    else:
        form = TargetForm()
    return render(request, 'roasted/add.html', {'form': form, 'section':{'title':'Add Track'}} )


def all_redirect(request):
    site  = getattr(settings,'SITE_URL','tracks.stowers.org')
    targets = Target.objects.all()

    paginator = Paginator(targets,25)
    try:
        page = int(request.GET.get('page','1'))
    except ValueError:
        page = 1

    #If requested page is out of range, deliver last page of results
    try:
        results = paginator.page(page)
    except (EmptyPage, InvalidPage):
        results = paginator.page(paginator.num_pages)

    total = len(targets)
    return render(request, 'roasted/all.html', {'site':site,'results':results, 'total':total})

def all_redirect_grid(request):
    site  = getattr(settings,'SITE_URL','tracks.stowers.org')
    targets = Target.objects.all()
    return JsonResponse(targets, safe=False)

def tracks_home(request):
    return render(request, 'roasted/index.html')

from django.db import models
from random import choice

# A simple URL shortener for use with tracks sevrer
# modified from http://github.com/rodbegbie/django-shorturl/tree/master

def new_key():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return choice(chars) + choice(chars) + choice(chars)

class Target(models.Model):
    """URL to be redirected"""

    key = models.CharField(max_length=30, primary_key=True, default=new_key())
    target_url = models.URLField(unique=True, db_index=True)
    added = models.DateTimeField(auto_now_add=True, editable=False)

    def trimmed_target_url(self):
        if len(self.target_url) < 50:
            return self.target_url
        else:
            return self.target_url[:50]+"..."

    trimmed_target_url.short_description = "Target URL"

    class Meta:
        ordering = ('-added',)

    def __str__(self):
        return "[%s] %s" % (self.key, self.trimmed_target_url())

class RedirectHit(models.Model):
    """Track hits to the redirect service"""
    target = models.ForeignKey(Target)
    hit_time = models.DateTimeField(auto_now_add=True, editable=False)
    referer = models.URLField(blank=True)
    remote_host = models.IPAddressField(blank=True)


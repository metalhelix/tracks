from django.test import TestCase
from django.core.urlresolvers import reverse
from roasted.models import Target, RedirectHit

class TargetTestCase(TestCase):
    def setUp(self):
        Target.objects.create(key="abc123", target_url="http://example.com")
        Target.objects.create(key="def456", target_url="http://example.com/path1")

    # def test_valid_redirect_create(self):
    #     data = {"key": "foo123", "url": "http://example.com"}
    #     self.assertEqual(Target.objects.count(),2)
    #     response = self.client.post(reverse())

    def test_add_redirect(self):
        resp = self.client.post(reverse('roasted-add_redirect'),
                                data={'key':'test_add134', 'target_url':'http://somewhere.com'})
        self.assertEqual(resp.status_code, 302)
        # add without specifying the key
        resp = self.client.post(reverse('roasted-add_redirect'), data={'target_url':'http://nowhere.com'})
        self.assertEqual(resp.status_code, 302)


    def test_fail_add_redirect(self):
        resp = self.client.post(reverse('roasted-add_redirect'), data={'key':'abc123', 'target_url':'http://nowhere.com'})
        self.assertEqual(resp.status_code, 200)
        print resp.context['form']
        self.assertEqual(len(resp.context['form']['error_message']), 1)

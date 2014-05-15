from django.test import TestCase
from django.contrib.auth.models import User
from form_builder.tests.factories import FormF, FieldF
from django.core.urlresolvers import reverse


class PermissionsTest(TestCase):
    fixtures = ['form-fixtures.json']
    csrf_checks = False

    @property
    def user(self):
        return User.objects.get(username='test1@example.com')
        
    def test_should_not_delete_others_form(self):
        user = User.objects.all()[1]
        form = FormF(owner=user)

        self.client.login(username="test1@example.com", password="1")
        url = reverse('form_builder:delete', args=(form.slug,))

        res = self.client.post(url, {})
        self.assertEquals(res.status_code, 404)

    def test_should_delete_own_form(self):
        form = FormF(owner=self.user)

        self.client.login(username="test1@example.com", password="1")
        url = reverse('form_builder:delete', args=(form.slug,))

        res = self.client.post(url, {})
        self.assertEquals(res.status_code, 302)
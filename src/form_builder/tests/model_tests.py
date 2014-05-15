from django.test import TestCase
from django.core.exceptions import ValidationError

from form_builder.models import FormResponse
from collab.django_factories import UserF
from form_builder.tests.factories import FormF, FieldF


class FieldTests(TestCase):
    def test_setting_choices(self):
        field = FieldF.build()
        field.choices = ['First', 'Second', 'Third']
        self.assertEqual(field._choices,
                         'First; Second; Third')


class FormResponseTests(TestCase):

    def test_collecting_users(self):
        form = FormF(collect_users=True)
        fr = FormResponse(form=form, user=None)

        try:
            fr.clean()
            self.fail("This should have thrown a ValidationError.")
        except ValidationError:
            pass

        fr.user = UserF(username='phil')
        try:
            fr.clean()
        except ValidationError:
            self.fail("This should not throw a ValidationError.")


class DuplicateTests(TestCase):

    def test_create_duplicate(self):
        form = FormF()
        field = FieldF.build(form=form)
        field.choices = ['First', 'Second', 'Third']
        field.save()
        dup = form.duplicate()

        self.assertIsNotNone(dup.pk)
        self.assertEqual(dup.owner, form.owner)
        self.assertEqual(dup.field_set.count(), form.field_set.count())

import re
import datetime

from django import forms
from django.forms.models import inlineformset_factory
from django.utils.html import urlize

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, Submit, \
        Button, HTML
from crispy_forms.bootstrap import FieldWithButtons, StrictButton

from . import models


class FormForm(forms.ModelForm):
    class Meta:
        model = models.Form
        fields = ('title', 'instructions', 'end_date', 'confirmation_text',
                  'collect_users', 'slug')

    def __init__(self, *args, **kwargs):
        super(FormForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field('title', css_class='input-xlarge'),
                Field('instructions', css_class='span5', rows=3),
                Field('confirmation_text', css_class='span5', rows=3),
                FieldWithButtons(
                    Field('end_date',
                          css_class="input-small end-date",
                          placeholder="never"),
                    StrictButton("<i class='icon-calendar'></i>",
                                 css_class="btn-datepicker")),
                Field('collect_users'),
            ),
        )


class FieldForm(forms.ModelForm):
    class Meta:
        model = models.Field

    def has_choices(self, field_type):
        return field_type == 'multiple-choice' or \
                field_type == 'checkboxes' or \
                field_type == 'dropdown'

    def create_layout(self, field_type):
        fields = [Field('field_type', value=field_type),
                  Field('label', css_class="input-xlarge",
                        placeholder="Untitled question")]
        if self.has_choices(field_type):
            fields.append(Field('_choices', css_class="input-xlarge choices"))
        fields.append(Field('help_text', css_class="input-xlarge"))
        fields.append(Field('required'))

        return Layout(Fieldset(models.Field.field_type_name(field_type),
                               *fields))

    def __init__(self, *args, **kwargs):
        field_type = kwargs.pop('field_type', None)

        super(FieldForm, self).__init__(*args, **kwargs)

        if field_type is None:
            field_type = (self.instance.field_type or
                          self.data.get("field_type", None) or
                          self.data.get("%s-field_type" % self.prefix, None))

        self.fields['help_text'].widget = forms.widgets.TextInput()
        self.fields['field_type'].widget = forms.widgets.HiddenInput()
        if self.has_choices(field_type):
            self.fields['_choices'].required = True

        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = self.create_layout(field_type)


FieldFormSet = inlineformset_factory(
    models.Form, models.Field, extra=0, form=FieldForm)


class TextField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = forms.Textarea
        super(TextField, self).__init__(*args, **kwargs)


class DateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = forms.DateInput
        super(DateField, self).__init__(*args, **kwargs)


class CheckboxField(forms.MultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = forms.CheckboxSelectMultiple
        super(CheckboxField, self).__init__(*args, **kwargs)


class RadioField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = forms.RadioSelect
        super(RadioField, self).__init__(*args, **kwargs)


class DropdownField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [('', '')] + (kwargs['choices'] or [])
        super(DropdownField, self).__init__(*args, **kwargs)


class ResponseForm(forms.Form):
    FORM_FIELDS = {
        'single-line': forms.CharField,
        'date': DateField,
        'multi-line': TextField,
        'multiple-choice': RadioField,
        'checkboxes': CheckboxField,
        'dropdown': DropdownField,
    }

    def create_layout(self, field_list):
        fields = []
        for field in field_list:
            fields.append(field)
        return Layout(*fields)

    def __init__(self, *args, **kwargs):
        self.custom_form = kwargs.pop('form')
        self.user = kwargs.pop('user')
        super(ResponseForm, self).__init__(*args, **kwargs)
        field_list_for_crispy = []

        for field in self.custom_form.field_set.all():
            field_dict = dict(label=field.label,
                              required=field.required)
            if field.help_text:
                field_dict['help_text'] = urlize(field.help_text)
            if field.default_value:
                field_dict['initial'] = field.default_value
            if field.choices:
                field_dict['choices'] = [(choice, choice)
                                         for choice in field.choices]
            if field.field_type == 'multiple-choice':
                num_choices = len(field_dict['choices'])
                if num_choices > 6:
                    field.field_type = 'dropdown'

            self.fields['custom_%s' % field.pk] = \
                self.FORM_FIELDS[field.field_type](**field_dict)
            field_list_for_crispy.append('custom_%s' % field.pk)
            if field.field_type == 'multi-line':
                # NOTE: In case you're tempted to add a "maxlength" paramater
                # to a multi-line input field, see the "NEWLINE ISSUE" note in
                # response-form-functions.js.
                field_list_for_crispy.append(HTML(
                    """<div class='textAreaCountMessage'><span \
                    class='help-block' id='custom_%s_textcount'>\
                    You may enter up to 2,500 characters into this \
                    box.</span></div>""" % field.pk))

        self.helper = FormHelper(self)
        response_layout = self.create_layout(field_list_for_crispy)
        self.helper.add_layout(response_layout)
        self.helper.add_input(Submit('submit', 'Save Response',
                                     css_class='btn-inverse'))
        self.helper.add_input(Button('cancel', 'Cancel',
                                     css_class='btn lightneutral50'))

    def save(self):

        def save_field_responses(form_response):
            data = self.cleaned_data
            pk_regex = re.compile(r'^custom_(\d+)$')

            for key, value in data.iteritems():
                pk_match = pk_regex.match(key)
                if pk_match:
                    field_pk = int(pk_match.group(1))
                    field = models.Field.objects.get(pk=field_pk)

                    if not isinstance(value, basestring):
                        if isinstance(value, datetime.date):
                            date_format = "%m/%d/%Y"
                            value = value.strftime(date_format)
                        elif isinstance(value, list):
                            value = "; ".join(value)
                        else:
                            value = ""

                    # see note in response-form-functions.js regarding
                    # newline issue
                    valStr = re.sub('\n\r', '', value)
                    if len(valStr) > 2500:
                        count_new_lines = value.count('\n') + value.count('\r')
                        value = value[:(2500 + count_new_lines)]

                    # Technically, since we're ignoring line breaks in the
                    # count of a field length, someone could append a whole
                    # lot of line breaks at the end of a long field and flood
                    # the database. The code below prevents that by stripping
                    # all whitespace at the beginning and end of the string.
                    value = value.strip()

                    field_response = models.FieldResponse(
                        form_response=form_response,
                        field=field,
                        value=value)
                    field_response.save()

        form_response = models.FormResponse(form=self.custom_form)
        if self.custom_form.collect_users:  # form is not anonymous
            form_response.user = self.user
            form_response.save()
            save_field_responses(form_response)
        else:  # form is anonymous
            if not models.AnonymousResponse.objects\
                   .check_dupe(self.custom_form.id, self.user.username):
                models.AnonymousResponse.objects.add_response(
                    self.custom_form.id, self.user.username)
                form_response.save()
                save_field_responses(form_response)

        return form_response

from copy import deepcopy
from datetime import date
from hashlib import md5
import re

from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext
from collab.settings import AUTH_USER_MODEL
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse


def unique_slug(item, slug_source, slug_field):
    """
    Ensures a unique slug field by appending an integer counter to duplicate
    slugs.

    The item's slug field is first prepopulated by slugify-ing the source
    field. If that value already exists, a counter is appended to the slug,
    and the counter incremented upward until the value is unique.

    For instance, if you save an object titled Daily Roundup, and the slug
    daily-roundup is already taken, this function will try daily-roundup-2,
    daily-roundup-3, daily-roundup-4, etc, until a unique value is found.

    Call from within a model's custom save() method like so:
    unique_slug(item, slug_source='field1', slug_field='field2')
    where the value of field slug_source will be used to prepopulate the value
    of slug_field.
    """
    if not getattr(item, slug_field):  # if it already has slug, do nothing.
        from django.template.defaultfilters import slugify
        slug = slugify(getattr(item, slug_source))
        itemModel = item.__class__
        # the following gets all existing slug values
        allSlugs = [sl.values()[0]
                    for sl in itemModel.objects.values(slug_field)]
        if slug in allSlugs:
            import re
            counterFinder = re.compile(r'-\d+$')
            counter = 2
            slug = "%s-%i" % (slug, counter)
            while slug in allSlugs:
                slug = re.sub(counterFinder, "-%i" % counter, slug)
                counter += 1
        setattr(item, slug_field, slug)


class Form(models.Model):
    owner = models.ManyToManyField(AUTH_USER_MODEL, null=True)
    title = models.CharField(_("Title"),
                             max_length=255,
                             help_text=_("Give your form a name."))
    slug = models.SlugField(_("URL slug"),
                            editable=True,
                            unique=True,
                            max_length=255,
                            blank=True,
                            help_text=_("Choose a custom URL slug for this "
                                        "form. For example, if you enter "
                                        "'my-first-form' (without the "
                                        "quotes), the link to share will be "
                                        "/forms/respond/my-first-form/. "
                                        "If not set, the default is to use "
                                        "the form's name in lowercase with "
                                        "dashes instead of spaces. If you "
                                        "change this after sending out "
                                        "a link for people to respond, "
                                        "those existing links will break, "
                                        "and you'll need to send the new "
                                        "link out to people."))
    instructions = models.TextField(_("Form instructions"),
                                    null=True,
                                    blank=True,
                                    help_text=_("Give your form some "
                                                "instructions."))
    confirmation_text = models.TextField(_("Confirmation message"),
                                         help_text=
                                         _("This text will be shown after the "
                                         "form is submitted. If you leave "
                                         "this blank, it will default to "
                                         "'Thank you for completing [form "
                                         "name].'"),
                                         null=True,
                                         blank=True)
    date_created = models.DateTimeField(_("Start date"),
                                        auto_now_add=True)
    end_date = models.DateField(_("End date"),
                                help_text=_("The form will not be shown after "
                                            "this date. Format: mm/dd/yyyy"),
                                blank=True,
                                null=True)
    collect_users = models.BooleanField(_("Collect respondent names"),
                                        help_text=_("Respondents' names will "
                                                    "be recorded. This "
                                                    "requires respondents to "
                                                    "be logged in."),
                                        default=True)
    email_on_response = models.BooleanField(_("Send email on response"),
                                            help_text=_("Send an email to you "
                                                        "when someone "
                                                        "responds to your "
                                                        "form."))

    def __unicode__(self):
        return unicode(self.title)

    def get_absolute_url(self):
        return reverse('form_builder:respond', args=(self.slug,))

    def owners(self):
        # Return a list of owners for the admin table
        return ", ".join(self.owner.values_list('email', flat=True))

    def save(self, *args, **kwargs):
        unique_slug(self, 'title', 'slug')
        super(Form, self).save(*args, **kwargs)

    def duplicate(self):
        field_set = self.field_set.all()
        obj = deepcopy(self)
        obj.pk = None
        obj.slug = None
        obj.title = obj.title + " (Copy)"
        obj.save()
        obj.owner = self.owner.all()
        for field in field_set:
            field.duplicate(obj)
        return obj

    def can_be_deleted(self):
        return self.response_set.count() == 0

    @property
    def is_closed(self):
        if self.end_date:
            return date.today() > self.end_date


class Field(models.Model):
    FIELD_TYPES = (
        ('single-line', _("Text box")),
        ('date', _("Date box")),
        ('multi-line', _("Paragraph text")),
        ('multiple-choice', _("Multiple choice")),
        ('checkboxes', _("Checkboxes")),
        ('dropdown', _("Dropdown")),
    )

    form = models.ForeignKey(Form)
    label = models.CharField(_("Question"),
                             max_length=255)
    help_text = models.TextField(_("Help Text"),
                                 null=True,
                                 blank=True)
    field_type = models.CharField(_("Field Type"),
                                  max_length=255,
                                  choices=FIELD_TYPES)
    required = models.BooleanField(_("Required"),
                                   default=False)
    default_value = models.CharField(_("Default Value"),
                                     max_length=255,
                                     null=True,
                                     blank=True)
    _choices = models.CharField(_("Choices"), max_length=1000, blank=True,
                                help_text="Options, separated by semicolons.")

    class Meta:
        order_with_respect_to = 'form'

    @classmethod
    def field_type_name(cls, field_type):
        return dict(cls.FIELD_TYPES).get(field_type, None)

    def __unicode__(self):
        return u"%s - %s" % (self.form.title, self.label)

    @property
    def choices(self):
        if self._choices:
            return re.compile(r"\s*;\s*").split(self._choices)
        else:
            return []

    @choices.setter
    def choices(self, choices):
        if choices:
            self._choices = "; ".join(choices)

    def duplicate(self, form=None):
        obj = self
        obj.pk = None
        if form:
            obj.form = form
        obj.save()
        return obj


class FormResponse(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True)
    form = models.ForeignKey(Form, related_name='response_set')
    submission_date = models.DateTimeField(_("Submission Date"),
                                           auto_now_add=True)
    archived = models.BooleanField(_("Archived"),
                                   help_text=_("Archive this response"),
                                   default=False)

    def clean(self):
        if self.form.collect_users and not self.user:
            raise ValidationError(
                "The associated form requires collection of users.")


class FieldResponse(models.Model):
    class Meta:
        ordering = ['form_response', 'field___order']

    form_response = models.ForeignKey(FormResponse)
    field = models.ForeignKey(Field)
    value = models.TextField(max_length=2 ** 24)


class AnonymousResponseManager(models.Manager):

    def create_hash(self, form_id, username):
        return md5(str(form_id) + username).hexdigest()

    def add_response(self, form_id, username):
        #creates md5 has of username and form id for anonymous log
        hash = AnonymousResponse.objects.create_hash(form_id, username)
        anonymous_response = AnonymousResponse(hash=hash)
        anonymous_response.save()

    def check_dupe(self, form_id, username):
        hash = self.create_hash(form_id, username)
        dupe = AnonymousResponse.objects.filter(hash=hash)
        print bool(dupe)
        return bool(dupe)


class AnonymousResponse(models.Model):
    """
    anonymous responses are saved when a user anonymously fills out a form.
    the log saves an md5 hash of the username of the person responding to
    a form and the id of the form itself. this makes it possible to have
    a reponse that is anonymous to the form creator but available in the case
    that this information is needed from security or human capital.

    to retreive the username stored in a hash, create a hash of all users
    with the form id of the form submission in question then find the
    response hash in that list of all users.

    this log also makes it possible to ensure that a user isn't able to
    respond to a form multiple times.
    """

    hash = models.CharField(max_length=32)
    submission_date = models.DateTimeField(auto_now_add=True)
    objects = AnonymousResponseManager()

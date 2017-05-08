import csv
import datetime
import re
import json
import unicodedata

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from core.models import Person
from core.notifications.email import EmailInfo
from core.notifications.models import Notification

from form_builder.models import Form, Field, FormResponse, AnonymousResponse
from form_builder.forms import FormForm, FieldForm, FieldFormSet, ResponseForm

# Helper functions


def create_templates():
    templates = [(field_type, FieldForm(field_type=field_type,
                  prefix="field_set-{{ i }}"))
                 for (field_type, _) in Field.FIELD_TYPES]
    return templates


def add_message(*args, **kwargs):
    if 'fail_silently' not in kwargs:
        kwargs['fail_silently'] = True
    return messages.add_message(*args, **kwargs)


def response_dict(**kwargs):
    return dict({
        'active_app': 'Form Builder',
        'app_link': reverse('form_builder:index')},
        **kwargs)

def normalize(string):
    return unicodedata.normalize('NFKD', string).encode('ascii','ignore').strip()

# Views


@login_required
def index(req):
    forms = req.user.form_set.all()
    return render_to_response('form_builder/index.html',
                              response_dict(forms=forms),
                              context_instance=RequestContext(req))


def redirect_to_index_or_form(req, form, fields, action="created"):
    if fields:
        add_message(req, messages.SUCCESS, "Your form has been " + action +
                    ".")
        return HttpResponseRedirect(reverse('form_builder:index'))
    else:
        add_message(req, messages.INFO, "Your form has been " + action + ". " +
                    "Before others can fill it out, you need to create some "
                    "fields.")
        return HttpResponseRedirect(reverse('form_builder:edit',
                                            args=[form.slug]))


@login_required
def new(req):
    form_form = FormForm(req.POST or None)
    field_form_set = FieldFormSet(req.POST or None)

    if form_form.is_valid() and field_form_set.is_valid():
        custom_form = form_form.save(commit=False)
        custom_form.save()
        custom_form.owner.add(req.user)
        custom_form.save()
        field_form_set = FieldFormSet(req.POST, instance=custom_form)
        if field_form_set.is_valid():
            fields = field_form_set.save()
        return redirect_to_index_or_form(req, custom_form, fields)

    context = RequestContext(req)
    context["formaction"] = "new"
    context['compact_header'] = 'compact-header'
    return render_to_response(
        'form_builder/form.html',
        response_dict(form=form_form,
                      fields=field_form_set,
                      form_action=reverse('form_builder:new'),
                      templates=create_templates()),
                      context_instance=context)


@login_required
def edit(req, id):
    # autosave functionality switch, in case something goes wrong
    # 0=off; 1=on
    use_form_autosave = 0

    custom_form = get_object_or_404(Form, owner=req.user, slug=id)
    form_form = FormForm(req.POST or None, instance=custom_form)
    field_form_set = FieldFormSet(req.POST or None, instance=custom_form)
    context = RequestContext(req)
    context['compact_header'] = 'compact-header'
    context["use_form_autosave"] = use_form_autosave
    context['custom_form'] = custom_form

    if form_form.is_valid() and field_form_set.is_valid():
        custom_form = form_form.save()
        if req.POST['owner_stub']:
            person = Person.objects.get(stub=req.POST.get('owner_stub', '').strip())
            collab_user = person.user
            custom_form.owner.add(collab_user)
        field_form_set.save()

        try:
            # In a case where someone created a form with no questions,
            # field_order would be blank. This would throw up an error to the
            # user, but the form data saves to the database fine. Easiest
            # solution is just to ignore the error; the expectation is that
            # most users will only save the form after adding at least a few
            # questions.
            custom_form.set_field_order(req.POST['field_order'].split(","))
        except:
            pass

        # FORM AUTOSAVE
        # =============
        # Assuming that the form saved properly, send response data back to
        # the client. This includes a dictionary containing a current queryset
        # of fields on the form.
        # This is used by the client to make DOM changes to match the current state of
        # the form.
        if (use_form_autosave == 1):
            time_now = datetime.datetime.now().strftime('%I:%M%p')
            field_list = Field.objects.filter(id=custom_form.id)
            field_dict = {}
            for field_instance in field_list:
                field_dict[field_instance.id] = field_instance.label
            responsedata = {
                "message": "Your form was updated at "
                           + re.sub(r'\A0', '', time_now.lower()) + ".",
                "formfields": field_dict,
            }
            return HttpResponse(json.dumps(responsedata),
                                content_type="application/json")
        else:
            add_message(req, messages.SUCCESS, "Your form has been updated.")
            return HttpResponseRedirect(reverse('form_builder:index'))

    elif form_form.errors or field_form_set.errors:
        # this code typically executes when someone has added a form field but
        # has not filled in a required element, such as the label; it ensures
        # that the code continues to run without bombing out
        if (use_form_autosave == 1):
            field_dict = {}
            responsedata = {
                "message": "Waiting to update form...",
                "formfields": field_dict,
            }
            return HttpResponse(json.dumps(responsedata),
                                content_type="application/json")

    return render_to_response(
        'form_builder/form.html',
        response_dict(form=form_form,
                      fields=field_form_set,
                      form_action=reverse('form_builder:edit',
                      args=[custom_form.slug]),
                      templates=create_templates()),
                      context_instance=context)


@login_required
def respond(req, id):
    user_form = get_object_or_404(Form, slug=id)
    already_responded = AnonymousResponse.objects.check_dupe(user_form.id,
                                                             req.user.username)
    if not already_responded:

        if req.GET:
            for field in user_form.field_set.all():
                if req.GET.has_key(field.label):
                    field.default_value = req.GET[field.label]
                    field.save()

        response_form = ResponseForm(
            req.POST or None, form=user_form, user=req.user)

        if not user_form.is_closed and response_form.is_valid():
            form_response = response_form.save()

            #set notification
            title = '%s %s submitted the "%s" form' % \
                (req.user.first_name, req.user.last_name, user_form)
            url = "/forms/results/%s/" % user_form.slug

            if user_form.owner.exists():
                if user_form.collect_users:
                    title = '%s %s submitted the "%s" form' % \
                        (req.user.first_name, req.user.last_name, user_form)
                    text_template = 'form_respond.txt'
                    html_template = 'form_respond.html'
                else:
                    title = 'Someone submitted the "%s" form' % user_form
                    text_template = 'form_respond_anonymous.txt'
                    html_template = 'form_respond_anonymous.html'

                for o in user_form.owner.all():
                    if o != req.user:
                        email_info = EmailInfo(
                            subject=title,
                            text_template='form_builder/email/%s' % text_template,
                            html_template='form_builder/email/%s' % html_template,
                            to_address=o.email
                        )
                        Notification.set_notification(req.user, req.user, "submitted",
                                                      user_form, o,
                                                      title, url, email_info)

            return HttpResponseRedirect(reverse('form_builder:form_thanks',
                                                args=[form_response.pk]))

        return render_to_response('form_builder/respond.html',
                                  {'user_form': user_form,
                                   'response_form': response_form},
                                  context_instance=RequestContext(req))
    else:
        context = RequestContext(req)
        context['form_title'] = user_form.title
        return render_to_response('form_builder/thanks.html', {}, context_instance=context)

@login_required
def form_thanks(req, id=None):
    if id:
        form_response = get_object_or_404(FormResponse, pk=id)
        return render_to_response('form_builder/thanks.html',
                                  {'form_response': form_response,
                                   'form': form_response.form},
                                  context_instance=RequestContext(req))
    else:
        form_response = None

    return render_to_response('form_builder/thanks.html', {},
                              context_instance=RequestContext(req))


@login_required
def results(req, id):
    form = get_object_or_404(Form, owner=req.user, slug=id)
    req_new = req.GET.get('new', '')

    response_count = form.response_set.count()

    new_responses = False
    for response in form.response_set.filter(archived=False):
        new_responses = form.response_set.filter(archived=False)

    context = RequestContext(req)
    context['compact_header'] = 'compact-header'

    if req_new != '':
        return render_to_response(
            'form_builder/results.html',
            response_dict(form=form,
                          responses=form.response_set.filter(archived=False),
                          fields=form.field_set.all(),
                          new=True,
                          new_responses=new_responses,
                          response_count=response_count),
            context_instance=context)
    else:
        return render_to_response(
            'form_builder/results.html',
            response_dict(form=form,
                          responses=form.response_set.all(),
                          fields=form.field_set.all(),
                          new=False,
                          new_responses=new_responses,
                          response_count=response_count),
            context_instance=context)


@login_required
def view_response(req, formid, resid):
    user_form = get_object_or_404(Form, owner=req.user, slug=formid)

    response_form = ResponseForm(
        req.POST or None, form=user_form, user=req.user)

    result = get_object_or_404(FormResponse, pk=resid)

    response_set = result.fieldresponse_set.all()

    for field_response in response_set:
        field_response.field.label = \
            field_response.field.label.replace(user_form.title + ' - ', '')

    return render_to_response('form_builder/respond.html',
                              response_dict(user_form=user_form,
                                            fields=user_form.field_set.all(),
                                            response_form=response_form,
                                            response=result,
                                            response_set=response_set,
                                            viewonly=True),
                              context_instance=RequestContext(req))


@login_required
def archive_result(req, id):
    result = get_object_or_404(FormResponse, pk=id)

    if result.archived is False:
        result.archived = True
        result.save()

    if req.META.get('HTTP_REFERER'):
        return HttpResponseRedirect(req.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect(reverse('form_builder:index'))


@login_required
def mark_result_as_new(req, id):
    result = get_object_or_404(FormResponse, pk=id)

    if result.archived:
        result.archived = False
        result.save()

    if req.META.get('HTTP_REFERER'):
        return HttpResponseRedirect(req.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect(reverse('form_builder:index'))


@login_required
def archive_all(req, id):
    form = get_object_or_404(Form, owner=req.user, slug=id)

    for response in form.response_set.filter(archived=False):
        response.archived = True
        response.save()

    if req.META.get('HTTP_REFERER'):
        return HttpResponseRedirect(req.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect(reverse('form_builder:index'))


@login_required
def results_csv(req, id):
    form = get_object_or_404(Form, owner=req.user, slug=id)
    req_new = req.GET.get('new', '')

    # Create the HttpResponse object with the appropriate CSV header.
    http_response = HttpResponse(content_type='text/csv')
    http_response['Content-Disposition'] = 'attachment; filename="results.csv"'

    writer = csv.writer(http_response)
    labels = [normalize(field.label) for field in form.field_set.all()]
    labels.insert(0, "Date/Time")
    if form.collect_users:
        labels.insert(0, "User")
    writer.writerow(labels)
    if req_new != '':
        for response in form.response_set.filter(archived=False):
            data = [normalize(field_response.value)
                    for field_response
                    in response.fieldresponse_set.all()]
            data.insert(0, response.submission_date)
            if form.collect_users:
                if response.user:
                    data.insert(0, normalize(response.user.first_name) + ' ' +
                                normalize(response.user.last_name))
                else:
                    data.insert(0, "anonymous")
            writer.writerow(data)
    else:
        for response in form.response_set.all():
            # This assumes a paste operation from an MS Office product
            # May want to be more sophisticated about encoding
            data = [normalize(field_response.value)
                    for field_response
                    in response.fieldresponse_set.all()]
            data.insert(0, response.submission_date)
            if form.collect_users:
                if response.user:
                    data.insert(0, normalize(response.user.first_name) + ' ' +
                                normalize(response.user.last_name))
                else:
                    data.insert(0, "anonymous")
            writer.writerow(data)

    return http_response


@login_required
@require_POST
def delete(req, id):
    form = get_object_or_404(Form, owner=req.user, slug=id)
    form.delete()
    add_message(req, messages.INFO, "Your form was deleted.")
    return HttpResponseRedirect(reverse('form_builder:index'))


@login_required
@require_POST
def duplicate(req, id):
    form = get_object_or_404(Form, owner=req.user, slug=id)
    form.duplicate()
    add_message(req, messages.INFO, "Your form was duplicated.")
    return HttpResponseRedirect(reverse('form_builder:index'))

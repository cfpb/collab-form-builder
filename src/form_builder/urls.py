from django.conf import settings
from django.conf.urls import patterns, include, url

urlpatterns = patterns('form_builder.views',
                       url(r'^$', 'index', name='index'),
                       url(r'^new/$', 'new', name='new'),
                       url(r'^edit/(?P<id>.+)/$', 'edit', name='edit'),
                       url(r'^delete/(?P<id>.+)/$', 'delete', name="delete"),
                       url(r'^duplicate/(?P<id>.+)/$', 'duplicate',
                           name='duplicate'),
                       url(r'^respond/(?P<id>.+)/$', 'respond',
                           name='respond'),
                       url(r'^thanks/(?P<id>.+)/$', 'form_thanks',
                           name='form_thanks'),
                       url(r'^thanks/$', 'form_thanks',
                           name='form_thanks'),
                       url(r'^results/(?P<id>.+)/$', 'results',
                           name='results'),
                       url(r'status/archive/(?P<id>.+)/$', 'archive_result',
                           name='status_archive'),
                       url(r'status/mark_new/(?P<id>.+)/$', 'mark_result_as_new',
                           name='status_mark_new'),
                       url(r'status/archive_all/(?P<id>.+)/$', 'archive_all',
                           name='archive_all'),
                       url(r'^csv/(?P<id>.+)/$', 'results_csv',
                           name='results_csv'),
                       url(r'^view_response/(?P<formid>.+)/(?P<resid>.+)/$',
                           'view_response', name='view_response')
                       )

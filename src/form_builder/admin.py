from form_builder.models import Form, Field, FormResponse, FieldResponse
from django.contrib import admin


class FieldInline(admin.StackedInline):
    model = Field
    extra = 1


class FormAdmin(admin.ModelAdmin):
    inlines = [FieldInline]
    list_display = ['title', 'owners', 'date_created', 'end_date']
    search_fields = ['title', 'owner__email']


class FieldResponseInline(admin.StackedInline):
    model = FieldResponse
    extra = 0


class FormResponseAdmin(admin.ModelAdmin):
    fields = ['form', 'user']
    inlines = [FieldResponseInline]
    list_display = ['form', 'user', 'submission_date']

admin.site.register(Form, FormAdmin)
admin.site.register(FormResponse, FormResponseAdmin)

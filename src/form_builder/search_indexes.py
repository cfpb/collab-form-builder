import datetime
from haystack import indexes
from form_builder.models import Form
from django.utils.html import strip_tags


class FormIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    display = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='instructions')
    index_name = indexes.CharField(indexed=False)
    index_priority = indexes.IntegerField(indexed=False)
    url = indexes.CharField(indexed=False, null=True)

    PRIORITY = 6

    def prepare_index_name(self, obj):
        return "Forms"

    def prepare_index_priority(self, obj):
        return self.PRIORITY

    def prepare_url(self, obj):
        return obj.get_absolute_url()

    def get_model(self):
        return Form

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def prepare_description(self, obj):
        return ""

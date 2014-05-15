import factory
from form_builder.models import Form, Field
from collab.django_factories import UserF


class FormF(factory.Factory):
    FACTORY_FOR = Form
    title = 'My Awesome Form'
    owner = factory.SubFactory(UserF)


class FieldF(factory.Factory):
    FACTORY_FOR = Field

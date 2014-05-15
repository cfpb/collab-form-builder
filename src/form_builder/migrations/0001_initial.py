# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Form'
        db.create_table('form_builder_form', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, blank=True)),
            ('instructions', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('confirmation_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('collect_users', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('email_on_response', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('form_builder', ['Form'])

        # Adding model 'Field'
        db.create_table('form_builder_field', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['form_builder.Form'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('help_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('field_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('_choices', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('form_builder', ['Field'])

        # Adding model 'FormResponse'
        db.create_table('form_builder_formresponse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(related_name='response_set', to=orm['form_builder.Form'])),
            ('submission_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('form_builder', ['FormResponse'])

        # Adding model 'FieldResponse'
        db.create_table('form_builder_fieldresponse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('form_response', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['form_builder.FormResponse'])),
            ('field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['form_builder.Field'])),
            ('value', self.gf('django.db.models.fields.TextField')(max_length=16777216)),
        ))
        db.send_create_signal('form_builder', ['FieldResponse'])


    def backwards(self, orm):
        # Deleting model 'Form'
        db.delete_table('form_builder_form')

        # Deleting model 'Field'
        db.delete_table('form_builder_field')

        # Deleting model 'FormResponse'
        db.delete_table('form_builder_formresponse')

        # Deleting model 'FieldResponse'
        db.delete_table('form_builder_fieldresponse')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'form_builder.field': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'Field'},
            '_choices': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['form_builder.Form']"}),
            'help_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'form_builder.fieldresponse': {
            'Meta': {'ordering': "['form_response', 'field___order']", 'object_name': 'FieldResponse'},
            'field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['form_builder.Field']"}),
            'form_response': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['form_builder.FormResponse']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'max_length': '16777216'})
        },
        'form_builder.form': {
            'Meta': {'object_name': 'Form'},
            'collect_users': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'confirmation_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'email_on_response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'form_builder.formresponse': {
            'Meta': {'object_name': 'FormResponse'},
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'response_set'", 'to': "orm['form_builder.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['form_builder']
# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Publishable.sort_order'
        db.add_column(u'core_publishable', 'sort_order',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)
        db.execute('UPDATE core_publishable SET sort_order = publish_from')


    def backwards(self, orm):
        # Deleting field 'Publishable.sort_order'
        db.delete_column(u'core_publishable', 'sort_order')


    models = {
    }

    complete_apps = ['core']

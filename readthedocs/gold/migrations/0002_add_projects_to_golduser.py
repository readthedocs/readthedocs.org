# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field projects on 'GoldUser'
        m2m_table_name = db.shorten_name(u'gold_golduser_projects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('golduser', models.ForeignKey(orm[u'gold.golduser'], null=False)),
            ('project', models.ForeignKey(orm[u'projects.project'], null=False))
        ))
        db.create_unique(m2m_table_name, ['golduser_id', 'project_id'])


    def backwards(self, orm):
        # Removing M2M table for field projects on 'GoldUser'
        db.delete_table(db.shorten_name(u'gold_golduser_projects'))


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'gold.golduser': {
            'Meta': {'object_name': 'GoldUser'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_4_digits': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'level': ('django.db.models.fields.CharField', [], {'default': "'supporter'", 'max_length': '20'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'gold_owners'", 'symmetrical': 'False', 'to': u"orm['projects.Project']"}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subscribed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'gold'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'projects.project': {
            'Meta': {'ordering': "('slug',)", 'object_name': 'Project'},
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'analytics_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'canonical_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'comment_moderation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'conf_py_file': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'copyright': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'default_branch': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'default_version': ('django.db.models.fields.CharField', [], {'default': "'latest'", 'max_length': '255'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'django_packages_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'documentation_type': ('django.db.models.fields.CharField', [], {'default': "'auto'", 'max_length': '20'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '20'}),
            'main_language_project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'translations'", 'null': 'True', 'to': u"orm['projects.Project']"}),
            'mirror': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'num_major': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'num_minor': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'num_point': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'privacy_level': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '20'}),
            'programming_language': ('django.db.models.fields.CharField', [], {'default': "'words'", 'max_length': '20', 'blank': 'True'}),
            'project_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'python_interpreter': ('django.db.models.fields.CharField', [], {'default': "'python'", 'max_length': '20'}),
            'related_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['projects.Project']", 'null': 'True', 'through': u"orm['projects.ProjectRelationship']", 'blank': 'True'}),
            'repo': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'repo_type': ('django.db.models.fields.CharField', [], {'default': "'git'", 'max_length': '10'}),
            'requirements_file': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'single_version': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'skip': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "'.rst'", 'max_length': '10'}),
            'theme': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '20'}),
            'use_system_packages': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'use_virtualenv': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'version_privacy_level': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '20'})
        },
        u'projects.projectrelationship': {
            'Meta': {'object_name': 'ProjectRelationship'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'superprojects'", 'to': u"orm['projects.Project']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subprojects'", 'to': u"orm['projects.Project']"})
        }
    }

    complete_apps = ['gold']

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('donate', '0007_add-impression-totals'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='supporterpromo',
            options={'ordering': ('-live',)},
        ),
        migrations.AddField(
            model_name='supporterpromo',
            name='programming_language',
            field=models.CharField(default=None, choices=[(b'words', b'Only Words'), (b'py', b'Python'), (b'js', b'Javascript'), (b'php', b'PHP'), (b'ruby', b'Ruby'), (b'perl', b'Perl'), (b'java', b'Java'), (b'go', b'Go'), (b'julia', b'Julia'), (b'c', b'C'), (b'csharp', b'C#'), (b'cpp', b'C++'), (b'objc', b'Objective-C'), (b'other', b'Other')], max_length=20, blank=True, null=True, verbose_name='Programming Language'),
        ),
    ]

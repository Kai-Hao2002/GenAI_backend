# Generated by Django 5.2.1 on 2025-06-14 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_emaillog_sent_at_alter_emaillog_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emaillog',
            name='tone',
        ),
    ]

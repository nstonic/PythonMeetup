# Generated by Django 4.2.2 on 2023-06-23 06:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tg_bot', '0004_speech_do_not_notify_alter_speech_speaker'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='speciality',
        ),
    ]
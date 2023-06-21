# Generated by Django 4.2.2 on 2023-06-21 16:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250, verbose_name='Мероприятие')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Краткое описание')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата и время начала')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата и время окончания')),
                ('image', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Фото/логотип')),
            ],
            options={
                'verbose_name': 'Мероприятие',
                'verbose_name_plural': 'Мероприятия',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.IntegerField(verbose_name='Идентификатор в телеграмме')),
                ('nickname', models.CharField(max_length=50, verbose_name='Никнейм')),
                ('fullname', models.CharField(blank=True, max_length=200, null=True, verbose_name='Полное имя')),
                ('age', models.PositiveIntegerField(blank=True, null=True, verbose_name='Возраст')),
                ('activity', models.TextField(blank=True, null=True, verbose_name='Род деятельности')),
                ('stack', models.CharField(blank=True, max_length=300, null=True, verbose_name='Стек')),
                ('hobby', models.CharField(blank=True, max_length=300, null=True, verbose_name='Хобби')),
                ('purpose', models.CharField(blank=True, max_length=300, null=True, verbose_name='Цель знакомства')),
                ('speciality', models.CharField(blank=True, max_length=250, null=True, verbose_name='Дополнительная информация')),
                ('registred_at', models.DateTimeField(auto_now=True, verbose_name='Дата и время регистрации')),
                ('is_admin', models.BooleanField(blank=True, default=False, null=True, verbose_name='Признак администратора')),
            ],
            options={
                'verbose_name': 'Участник',
                'verbose_name_plural': 'Участники',
            },
        ),
        migrations.CreateModel(
            name='Speech',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250, verbose_name='Тема доклада')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Краткое описание доклада')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Начало доклада')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='Окончание доклада')),
                ('image', models.ImageField(blank=True, null=True, upload_to='', verbose_name='Аватар')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='speeches', to='tg_bot.event', verbose_name='Мероприятие')),
                ('speaker', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='speaker_events', to='tg_bot.user', verbose_name='Докладчик')),
            ],
            options={
                'verbose_name': 'Доклад',
                'verbose_name_plural': 'Доклады',
            },
        ),
        migrations.AddField(
            model_name='event',
            name='members',
            field=models.ManyToManyField(related_name='events', to='tg_bot.user', verbose_name='Участники мероприятия'),
        ),
        migrations.AddField(
            model_name='event',
            name='organizers',
            field=models.ManyToManyField(related_name='org_events', to='tg_bot.user', verbose_name='Организаторы'),
        ),
    ]

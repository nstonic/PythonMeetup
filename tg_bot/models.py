from django.db import models
from django.db.models import QuerySet
from django.utils.timezone import now


class User(models.Model):
    telegram_id = models.IntegerField(
        verbose_name='Идентификатор в телеграмме',
    )
    nickname = models.CharField(
        max_length=50,
        verbose_name='Никнейм',
    )
    fullname = models.CharField(
        max_length=200,
        verbose_name='Полное имя',
        blank=True,
        null=True,
    )
    age = models.PositiveIntegerField(
        verbose_name='Возраст',
        blank=True,
        null=True,
    )
    activity = models.TextField(
        verbose_name='Род деятельности',
        blank=True,
        null=True,
    )
    stack = models.CharField(
        max_length=300,
        verbose_name='Стек',
        blank=True,
        null=True,
    )
    hobby = models.CharField(
        max_length=300,
        verbose_name='Хобби',
        blank=True,
        null=True,
    )
    purpose = models.CharField(
        max_length=300,
        verbose_name='Цель знакомства',
        blank=True,
        null=True,
    )
    registred_at = models.DateTimeField(
        verbose_name='Дата и время регистрации',
        auto_now=True,
    )
    is_admin = models.BooleanField(
        verbose_name='Признак администратора',
        default=False
    )

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self):
        adm = 'АДМИНИСТРАТОР' if self.is_admin else ''
        return f'{adm} {self.nickname} - {self.fullname}'


class EventQuerySet(QuerySet):

    def get_current(self):
        right_now = now()
        return self.filter(
            started_at__lte=right_now,
            finished_at__gte=right_now
        ).first()

    def get_current_or_closest(self):
        right_now = now()
        event = self.filter(
            started_at__lte=right_now,
            finished_at__gte=right_now
        ).first()
        if not event:
            event = self.filter(
                started_at__gte=right_now
            ).order_by("started_at").first()
        return event

    def filter_futures(self):
        return self.filter(started_at__gt=now())


class Event(models.Model):
    title = models.CharField(
        max_length=250,
        verbose_name='Мероприятие',
    )
    description = models.TextField(
        verbose_name='Краткое описание',
        blank=True,
        null=True,
    )
    started_at = models.DateTimeField(
        verbose_name='Дата и время начала',
        blank=True,
        null=True,
    )
    finished_at = models.DateTimeField(
        verbose_name='Дата и время окончания',
        blank=True,
        null=True,
    )
    members = models.ManyToManyField(
        User,
        verbose_name='Участники мероприятия',
        related_name='events',
    )
    organizers = models.ManyToManyField(
        User,
        verbose_name='Организаторы',
        related_name='org_events',
    )
    image = models.ImageField(
        verbose_name='Фото/логотип',
        blank=True,
        null=True,
    )

    objects = EventQuerySet.as_manager()

    def __str__(self):
        return f'{self.started_at} - {self.title}'

    def get_organizer(self):
        set_organizers = self.organizers.get_queryset()
        return ', '.join([
            str(organizer.fullname)
            for organizer in set_organizers
        ])

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'


class SpeechQuerySet(QuerySet):

    def get_current(self, moment=now()):
        return self.filter(
            started_at__lte=moment,
            finished_at__gte=moment
        ).order_by('started_at').first()

    def filter_futures(self):
        right_now = now()
        return self.filter(started_at__gt=right_now)


class Speech(models.Model):
    title = models.CharField(
        max_length=250,
        verbose_name='Тема доклада',
    )
    description = models.TextField(
        verbose_name='Краткое описание доклада',
        blank=True,
        null=True,
    )
    started_at = models.DateTimeField(
        verbose_name='Начало доклада',
        blank=True,
        null=True,
    )
    finished_at = models.DateTimeField(
        verbose_name='Окончание доклада',
        blank=True,
        null=True,
    )
    event = models.ForeignKey(
        Event,
        verbose_name='Мероприятие',
        related_name='speeches',
        on_delete=models.PROTECT,
    )
    speaker = models.ForeignKey(
        User,
        verbose_name='Докладчик',
        related_name='speaker_speeches',
        on_delete=models.PROTECT,
    )
    image = models.ImageField(
        verbose_name='Аватар',
        blank=True,
        null=True,
    )
    do_not_notify = models.BooleanField(
        verbose_name='Не предлагать продление',
        default=False
    )

    objects = SpeechQuerySet.as_manager()

    def __str__(self):
        return f'{self.started_at.strftime("%H:%M")}-{self.finished_at.strftime("%H:%M")} - {self.speaker} - {self.title}'

    class Meta:
        verbose_name = 'Доклад'
        verbose_name_plural = 'Доклады'

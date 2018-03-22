import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.db.models.signals import post_save  # , pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

GROUP_ADMIN_ID = 'Admin'
GROUP_TEACHER_ID = 'Teacher'
GROUP_STUDENT_ID = 'Student'
GROUP_PARENT_ID = 'Parent'


def create_default_groups():
    Group.objects.get_or_create(name=GROUP_TEACHER_ID)
    Group.objects.get_or_create(name=GROUP_STUDENT_ID)
    Group.objects.get_or_create(name=GROUP_PARENT_ID)


class Class(models.Model):
    name = models.CharField(max_length=20, unique=True, blank=False, null=False)


class Subject(models.Model):
    name = models.CharField(max_length=20, unique=True, blank=False, null=False)


class UserManager(BaseUserManager):
    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()

        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email,
                          username=email,  # FIXME
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class User(AbstractUser):
    objects = UserManager()

    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'

    REQUIRED_FIELDS = []

    # username = models.CharField(max_length=30, blank=True)
    first_name = models.CharField(_('first name'), max_length=100, blank=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True)
    is_staff = models.BooleanField(
        _('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'),
    )
    is_active = models.BooleanField(
        _('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    parents = models.ManyToManyField('self',
                                     symmetrical=False,
                                     related_name='children',
                                     )

    # Only for students:
    attends = models.ForeignKey(Class,
                                related_name='students',
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                )
    subjects = models.ManyToManyField(Subject,
                                      related_name='students',
                                      )


class ClassTeacherSubject(models.Model):
    teacher = models.ForeignKey(User,
                                related_name='classes_subjects',
                                on_delete=models.CASCADE,
                                null=False,
                                blank=False,
                                )
    subject = models.ForeignKey(Subject,
                                related_name='classes_teachers',
                                on_delete=models.CASCADE,
                                null=False,
                                blank=False,
                                )
    teaches_in = models.ForeignKey(Class,
                                   related_name='teachers_subjects',
                                   on_delete=models.CASCADE,
                                   null=False,
                                   blank=False,
                                   )

    class Meta:
        unique_together = ('teacher', 'subject', 'teaches_in')


# class Profile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         primary_key=True,
#     )


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)


class Notification(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    date = models.DateTimeField(default=None, null=True)
    target_student = models.ForeignKey(User,
                                       related_name='notifications_received',
                                       default=None,
                                       on_delete=models.SET_NULL,
                                       null=True,
                                       blank=True)
    target_class = models.ForeignKey(Class,
                                     on_delete=models.SET_NULL,
                                     default=None,
                                     null=True,
                                     blank=True)
    subject = models.ForeignKey(Subject,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                default=None,
                                )
    icon = models.CharField(max_length=300, blank=True, null=True)

    TYPE_GENERIC = 'GENERIC'
    TYPE_EXAM = 'EXAM'
    TYPE_TASK = 'TASK'
    TYPE_ATTENDANCE = 'ATTENDANCE'

    TYPES_CHOICES = (
        (TYPE_GENERIC, 'Generic'),
        (TYPE_EXAM, 'Exam'),
        (TYPE_TASK, 'Task'),
        (TYPE_ATTENDANCE, 'Attendance'),
    )

    type = models.CharField(max_length=10,
                            choices=TYPES_CHOICES,
                            default=TYPE_GENERIC,
                            )

    custom_fields = JSONField(default=dict)

    def clean(self):
        if self.target_student is None and self.target_class is None:
            raise ValidationError(_('Notification may have directed to a '
                                    'student or a class.'))


class Schedule(models.Model):
    MONDAY = 'MONDAY'
    TUESDAY = 'TUESDAY'
    WEDNESDAY = 'WEDNESDAY'
    THURSDAY = 'THURSDAY'
    FRIDAY = 'FRIDAY'

    DAY_CHOICES = (
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
    )

    ORDER = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6),
        (7, 7),
        (8, 8),
        (9, 9),
        (10, 10),
    )

    day = models.CharField(max_length=10,
                           choices=DAY_CHOICES,
                           null=False,
                           blank=False
                           )

    order = models.IntegerField(choices=ORDER,
                                null=False,
                                blank=False)

    time = models.TimeField(null=False,
                            blank=False,
                            )

    class_teacher_subject = models.ForeignKey(ClassTeacherSubject,
                                              # related_name='schedule_class_teacher_subject',
                                              on_delete=models.CASCADE,
                                              null=False,
                                              blank=False,
                                              )

    class Meta:
        unique_together = ('day', 'time', 'order', 'class_teacher_subject')


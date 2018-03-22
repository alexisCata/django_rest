import os
import datetime
import pytz

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from datetime import time

from core.models import (User,
                         Class,
                         Subject,
                         ClassTeacherSubject,
                         Schedule,
                         create_default_groups,
                         GROUP_TEACHER_ID,
                         GROUP_STUDENT_ID,
                         GROUP_PARENT_ID,
                         )
from chat.database import client


def insert_data_for_tests():
    group_teachers = Group.objects.get(name=GROUP_TEACHER_ID)
    group_students = Group.objects.get(name=GROUP_STUDENT_ID)
    group_parents = Group.objects.get(name=GROUP_PARENT_ID)

    mates = Subject.objects.create(name='Mates')
    lengua = Subject.objects.create(name='Lengua')
    ingles = Subject.objects.create(name='Inglés')
    sociales = Subject.objects.create(name='Ciencias sociales')

    profe_mates = User.objects.create_user(
        email='mates@school.com',
        password='password123',
        first_name='Profe mates',
    )
    profe_mates.groups.add(group_teachers)

    profe_lengua = User.objects.create_user(
        email='lengua@school.com',
        password='password123',
        first_name='Profe lengua',
    )
    profe_lengua.groups.add(group_teachers)

    profe_ingles_sociales = User.objects.create_user(
        email='ingles.sociales@school.com',
        password='password123',
        first_name='Profe inglés y ciencias sociales',
    )
    profe_ingles_sociales.groups.add(group_teachers)

    madre_javier = User.objects.create_user(
        email='javier.madre@school.com',
        password='password123',
        first_name='Madre Javier',
    )
    madre_javier.groups.add(group_parents)

    madre_alexis = User.objects.create_user(
        email='alexis.madre@school.com',
        password='password123',
        first_name='Madre Alexis',
    )
    madre_alexis.groups.add(group_parents)

    madre_cristobal = User.objects.create_user(
        email='cristobal.madre@school.com',
        password='password123',
        first_name='Madre Cristóbal',
    )
    madre_cristobal.groups.add(group_parents)

    madre_belen = User.objects.create_user(
        email='belen.madre@school.com',
        password='password123',
        first_name='Madre Belén',
    )
    madre_belen.groups.add(group_parents)

    padre_javier = User.objects.create_user(
        email='javier.padre@school.com',
        password='password123',
        first_name='Padre Javier',
    )
    padre_javier.groups.add(group_parents)

    padre_alexis = User.objects.create_user(
        email='alexis.padre@school.com',
        password='password123',
        first_name='Padre Alexis',
    )
    padre_alexis.groups.add(group_parents)

    padre_cristobal = User.objects.create_user(
        email='cristobal.padre@school.com',
        password='password123',
        first_name='Padre de Cristóbal',
    )
    padre_cristobal.groups.add(group_parents)

    padre_belen = User.objects.create_user(
        email='belen.padre@school.com',
        password='password123',
        first_name='Padre Belén',
    )
    padre_belen.groups.add(group_parents)

    javier = User.objects.create_user(
        email='javier@school.com',
        password='password123',
        first_name='Javier',
    )
    javier.groups.add(group_students)
    javier.parents.add(padre_javier)
    javier.parents.add(madre_javier)
    javier.subjects.add(mates)
    javier.subjects.add(lengua)

    alexis = User.objects.create_user(
        email='alexis@school.com',
        password='password123',
        first_name='Alexis',
    )
    alexis.groups.add(group_students)
    alexis.parents.add(padre_alexis)
    alexis.parents.add(madre_alexis)
    alexis.subjects.add(mates)
    alexis.subjects.add(lengua)
    alexis.subjects.add(ingles)

    alexis2 = User.objects.create_user(
        email='alexis2@school.com',
        password='password123',
        first_name='Alexis 2',
    )
    alexis2.groups.add(group_students)
    alexis2.parents.add(padre_alexis)
    alexis2.parents.add(madre_alexis)
    alexis2.subjects.add(mates)
    alexis2.subjects.add(lengua)

    cristobal = User.objects.create_user(
        email='cristobal@school.com',
        password='password123',
        first_name='Cristóbal',
    )
    cristobal.groups.add(group_students)
    cristobal.parents.add(padre_cristobal)
    cristobal.parents.add(madre_cristobal)
    cristobal.subjects.add(mates)
    cristobal.subjects.add(lengua)

    belen = User.objects.create_user(
        email='belen@school.com',
        password='password123',
        first_name='Belén',
    )
    belen.groups.add(group_students)
    belen.parents.add(padre_belen)
    belen.parents.add(madre_belen)
    belen.subjects.add(mates)
    belen.subjects.add(lengua)

    c = Class.objects.create(name='1A')

    ct1a = ClassTeacherSubject.objects.create(
        teacher=profe_mates,
        subject=mates,
        teaches_in=c
    )
    ClassTeacherSubject.objects.create(
        teacher=profe_lengua,
        subject=lengua,
        teaches_in=c
    )
    ClassTeacherSubject.objects.create(
        teacher=profe_ingles_sociales,
        subject=ingles,
        teaches_in=c
    )
    ClassTeacherSubject.objects.create(
        teacher=profe_ingles_sociales,
        subject=sociales,
        teaches_in=c
    )

    javier.attends = c
    javier.save()
    alexis.attends = c
    alexis.save()

    c = Class.objects.create(name='1B')

    ct1b = ClassTeacherSubject.objects.create(
        teacher=profe_mates,
        subject=mates,
        teaches_in=c
    )
    ClassTeacherSubject.objects.create(
        teacher=profe_lengua,
        subject=lengua,
        teaches_in=c
    )
    ClassTeacherSubject.objects.create(
        teacher=profe_ingles_sociales,
        subject=sociales,
        teaches_in=c
    )

    cristobal.attends = c
    cristobal.save()
    belen.attends = c
    belen.save()

    c = Class.objects.create(name='2A')

    ct2a = ClassTeacherSubject.objects.create(
        teacher=profe_mates,
        subject=mates,
        teaches_in=c
    )
    ClassTeacherSubject.objects.create(
        teacher=profe_lengua,
        subject=lengua,
        teaches_in=c
    )
    ClassTeacherSubject.objects.create(
        teacher=profe_ingles_sociales,
        subject=sociales,
        teaches_in=c
    )

    alexis2.attends = c
    alexis2.save()

    t1 = time(9, 0)

    Schedule.objects.create(class_teacher_subject=ct1a,
                            day=Schedule.DAY_CHOICES[0][0],
                            time=t1,
                            order=Schedule.ORDER[0][1]
                            )
    t2 = time(10, 0)
    Schedule.objects.create(class_teacher_subject=ct1b,
                            day=Schedule.DAY_CHOICES[0][0],
                            time=t2,
                            order=Schedule.ORDER[1][1]
                            )
    t3 = time(11, 0)
    Schedule.objects.create(class_teacher_subject=ct2a,
                            day=Schedule.DAY_CHOICES[0][0],
                            time=t3,
                            order=Schedule.ORDER[2][1]
                            )

    client.drop_database(settings.MONGO_DATABASE)
    db = client[settings.MONGO_DATABASE]

    chat_history = [
        {
            'user_from': belen.id,
            'user_to': cristobal.id,
            'conversation_id': '{}-{}'.format(
                min(belen.id, cristobal.id), max(belen.id, cristobal.id)),
            'message': 'hola!',
            'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 0, 0,
                                           pytz.UTC),
        },
        {
            'user_from': belen.id,
            'user_to': cristobal.id,
            'conversation_id': '{}-{}'.format(
                min(belen.id, cristobal.id), max(belen.id, cristobal.id)),
            'message': ':)',
            'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 1, 0,
                                           pytz.UTC),
        },
        {
            'user_from': javier.id,
            'user_to': alexis.id,
            'conversation_id': '{}-{}'.format(
                min(javier.id, alexis.id), max(javier.id, alexis.id)),
            'message': 'hello!',
            'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 1, 0,
                                           pytz.UTC),
        },
        {
            'user_from': cristobal.id,
            'user_to': belen.id,
            'conversation_id': '{}-{}'.format(
                min(belen.id, cristobal.id), max(belen.id, cristobal.id)),
            'message': 'hey!',
            'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 2, 0,
                                           pytz.UTC),
        },
        {
            'user_from': javier.id,
            'user_to': belen.id,
            'conversation_id': '{}-{}'.format(
                min(belen.id, javier.id), max(belen.id, javier.id)),
            'message': 'buenas!',
            'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 3, 0,
                                           pytz.UTC),
        },
    ]

    col = db.chats_history
    col.insert_many(chat_history)


def init_database():
    create_default_groups()

    if not User.objects.filter(email='team@cathedralsw.com').count():
        User.objects.create_superuser(
            email='team@cathedralsw.com', password='password123')

    else:
        print('Admin accounts can only be initialized if no accounts exist')


class Command(BaseCommand):
    def handle(self, *args, **options):
        init_database()

        if os.environ.get('SCHOOL_TEST', ''):
            insert_data_for_tests()

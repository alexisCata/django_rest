import datetime
import pytz
import unittest.mock as mock

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.core.urlresolvers import resolve
from django.contrib.auth.models import Group

from rest_framework.test import APIRequestFactory, force_authenticate

from rest_framework_jwt.views import (
    obtain_jwt_token, refresh_jwt_token, verify_jwt_token
)

from core.models import (User,
                         Notification,
                         Class,
                         Subject,
                         create_default_groups,
                         GROUP_TEACHER_ID,
                         GROUP_STUDENT_ID,
                         GROUP_PARENT_ID,
                         )
from chat.database import client

from .views import (NotificationsService,
                    AuthUser,
                    ClassesService,
                    UsersService,
                    # ChatsService,
                    )


ISO_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class AuthTest(TestCase):

    def setUp(self):
        from core.management.commands.initadmin import (insert_data_for_tests,
                                                        init_database)
        init_database()
        insert_data_for_tests()

        self.user = User.objects.get(
            email='alexis.padre@school.com')

    def test_auth_route(self):
        found = resolve('/api/auth/')

        self.assertEqual(found.func, obtain_jwt_token)

    def test_auth(self):
        c = Client()
        response = c.post(
            '/api/auth/',
            {
                'email': 'cristobal.padre@school.com',
                'password': 'password123',
            }
        )
        self.assertEqual(response.status_code, 200)

        self.assertTrue('token' in response.json())

    def test_refresh_route(self):
        found = resolve('/api/auth/refresh/')

        self.assertEqual(found.func, refresh_jwt_token)

    def test_refresh(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'cristobal.padre@school.com',
                'password': 'password123',
            }
        )

        response = c.post(
            '/api/auth/refresh/',
            {
                'token': r1.json()['token']
            }
        )
        self.assertEqual(response.status_code, 200)

        self.assertTrue('token' in response.json())

    def test_verify_route(self):
        found = resolve('/api/auth/verify/')

        self.assertEqual(found.func, verify_jwt_token)

    def test_verify(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'cristobal.padre@school.com',
                'password': 'password123',
            }
        )

        response = c.post(
            '/api/auth/verify/',
            {
                'token': r1.json()['token']
            }
        )
        self.assertEqual(response.status_code, 200)

        self.assertTrue('token' in response.json())

    def test_get_current_user_route(self):
        found = resolve('/api/auth/user/')

        # self.assertEqual(found.func, AuthUser.as_view())

    def test_get_current_user(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'alexis.padre@school.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/auth/user/',
            {},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(result['id'], self.user.id)
        self.assertEqual(result['first_name'], self.user.first_name)
        self.assertEqual(result['last_name'], self.user.last_name)
        self.assertEqual(result['groups'], [{'name': 'Parent'}])
        self.assertTrue('children' in result)
        self.assertEqual(len(result['children']), 2)
        self.assertTrue('attends' in result['children'][0])


class NotificationTest(TestCase):

    def setUp(self):
        from core.management.commands.initadmin import (insert_data_for_tests,
                                                        init_database)
        init_database()
        insert_data_for_tests()

        # self.user_admin = User.objects.get(email='team@cathedralsw.com')
        self.user_owner = User.objects.get(email='mates@school.com')
        self.parent_target_student = User.objects.get(
            email='cristobal.padre@school.com')
        self.target_student = User.objects.get(email='cristobal@school.com')
        self.other_user = User.objects.get(email='alexis.padre@school.com')
        self.other_student = User.objects.get(email='alexis@school.com')
        self.parent_target_student_class = User.objects.get(
            email='belen.madre@school.com')
        self.target_student_class = User.objects.get(email='belen@school.com')
        self.target_class = Class.objects.get(name='1B')
        self.other_class = Class.objects.get(name='1A')
        self.mates = Subject.objects.get(name='Mates')
        self.lengua = Subject.objects.get(name='Lengua')
        self.ingles = Subject.objects.get(name='Inglés')

    def test_notification_route(self):
        found = resolve('/api/notifications/')

        # self.assertEqual(found.func, NotificationsService.as_view())

    # def test_notification_get_unauthorized(self):
    #     factory = APIRequestFactory()
    #     request = factory.get('/api/notifications/', {})

    #     view = NotificationsService.as_view({'get': 'list'})

    #     response = view(request)

    #     self.assertEqual(response.status_code, 401)

    def test_notification_get_list(self):
        notification1 = Notification.objects.create(
            title='New test task 1',
            owner=self.user_owner,
            description='A difficult test task 1',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
        )
        notification2 = Notification.objects.create(
            title='New test task 2',
            owner=self.other_user,
            description='A difficult test task 2',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
        )
        notification3 = Notification.objects.create(
            title='New test task 3',
            owner=self.user_owner,
            description='A difficult test task 3',
            date=datetime.datetime(2017, 8, 3, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
        )

        factory = APIRequestFactory()
        request = factory.get('/api/notifications/')
        force_authenticate(request, user=self.user_owner)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 2)

        self.assertEqual(result[0]['title'], 'New test task 3')
        # self.assertEqual(result[0]['owner'], self.user_owner.id)
        self.assertEqual(result[0]['owner']['id'],
                         self.user_owner.id)
        self.assertEqual(result[0]['owner']['first_name'],
                         self.user_owner.first_name)
        self.assertEqual(result[0]['owner']['last_name'],
                         self.user_owner.last_name)
        self.assertEqual(result[0]['description'], 'A difficult test task 3')
        self.assertEqual(result[0]['date'], '2017-08-03T00:00:00Z')
        # self.assertEqual(result[0]['target_class'], self.target_class.id)
        self.assertEqual(result[0]['target_class']['id'], self.target_class.id)
        self.assertEqual(result[0]['target_class']['name'],
                         self.target_class.name)
        self.assertEqual(result[0]['target_student'], None)
        self.assertEqual(result[1]['title'], 'New test task 1')
        self.assertEqual(result[1]['owner']['id'],
                         self.user_owner.id)
        self.assertEqual(result[1]['owner']['first_name'],
                         self.user_owner.first_name)
        self.assertEqual(result[1]['owner']['last_name'],
                         self.user_owner.last_name)
        self.assertEqual(result[1]['description'], 'A difficult test task 1')
        self.assertEqual(result[1]['date'], '2017-08-01T00:00:00Z')
        self.assertEqual(result[1]['target_class'], None)
        # self.assertEqual(result[1]['target_student'], self.target_student.id)
        self.assertEqual(result[1]['target_student']['id'],
                         self.target_student.id)
        self.assertEqual(result[1]['target_student']['first_name'],
                         self.target_student.first_name)
        self.assertEqual(result[1]['target_student']['last_name'],
                         self.target_student.last_name)

    def test_notification_get_list_filter_student(self):
        notification1 = Notification.objects.create(
            title='New test task 1',
            owner=self.user_owner,
            description='A difficult test task 1',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='New test task 4',
            owner=self.user_owner,
            description='A difficult test task 4',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.other_student,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='New test task 2',
            owner=self.user_owner,
            description='A difficult test task 2',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=self.target_student_class,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='New test task 5',
            owner=self.user_owner,
            description='A difficult test task 5',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.other_class,
            target_student=None,
            type=Notification.TYPE_TASK,
        )
        notification3 = Notification.objects.create(
            title='New test exam 3',
            owner=self.user_owner,
            description='A difficult test exam 3',
            date=datetime.datetime(2017, 8, 3, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            type=Notification.TYPE_EXAM,
        )

        factory = APIRequestFactory()

        #######################################################################
        request = factory.get('/api/notifications/',
                              {
                                  'student': self.target_student.id,
                              })
        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data
        # print(result)

        self.assertEqual(len(result), 2)

        for n in result:
            if n['target_student'] is not None:
                self.assertEqual(n['target_student']['id'],
                                 self.target_student.id)

            else:
                self.assertEqual(n['target_class']['id'],
                                 self.target_class.id)

        #######################################################################
        request = factory.get('/api/notifications/',
                              {
                                  'student': self.other_student.id,
                              })
        force_authenticate(request, user=self.other_user)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data
        # print(result)

        self.assertEqual(len(result), 2)

        for n in result:
            if n['target_student'] is not None:
                self.assertEqual(n['target_student']['id'],
                                 self.other_student.id)

            else:
                self.assertEqual(n['target_class']['id'],
                                 self.other_class.id)

    def test_notification_get_list_filter_subject(self):
        notification1 = Notification.objects.create(
            title='New test task 1',
            owner=self.user_owner,
            description='A difficult test task 1',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='New test task 4',
            owner=self.user_owner,
            description='A difficult test task 4',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=self.target_student,
            subject=self.lengua,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='New test task 2',
            owner=self.user_owner,
            description='A difficult test task 2',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='New test task 5',
            owner=self.user_owner,
            description='A difficult test task 5',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification3 = Notification.objects.create(
            title='New test exam 3',
            owner=self.user_owner,
            description='A difficult test exam 3',
            date=datetime.datetime(2017, 8, 3, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.ingles,
            type=Notification.TYPE_EXAM,
        )

        factory = APIRequestFactory()

        #######################################################################
        request = factory.get('/api/notifications/',
                              {
                                  'subject': self.mates.id,
                              })
        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 3)

        for n in result:
            self.assertEqual(n['subject']['id'], self.mates.id)
            self.assertEqual(n['subject']['name'], self.mates.name)

        #######################################################################
        request = factory.get('/api/notifications/',
                              {
                                  'subject': self.lengua.id,
                              })
        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 1)

        for n in result:
            self.assertEqual(n['subject']['id'], self.lengua.id)
            self.assertEqual(n['subject']['name'], self.lengua.name)

    def test_notification_get_list_filter_type(self):
        notification1 = Notification.objects.create(
            title='New test task 1',
            owner=self.user_owner,
            description='A difficult test task 1',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='Attendance',
            owner=self.user_owner,
            description='Your son did not attended classes today.',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=self.target_student,
            subject=self.lengua,
            type=Notification.TYPE_ATTENDANCE,
        )
        notification2 = Notification.objects.create(
            title='New test task 2',
            owner=self.user_owner,
            description='A difficult test task 2',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='New test task 5',
            owner=self.user_owner,
            description='A difficult test task 5',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification3 = Notification.objects.create(
            title='New test exam 3',
            owner=self.user_owner,
            description='A difficult test exam 3',
            date=datetime.datetime(2017, 8, 3, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.ingles,
            type=Notification.TYPE_EXAM,
        )

        factory = APIRequestFactory()

        #######################################################################
        request = factory.get('/api/notifications/',
                              {
                                  'type': Notification.TYPE_TASK,
                              })
        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 3)

        for n in result:
            self.assertEqual(n['type'], Notification.TYPE_TASK)

        #######################################################################
        request = factory.get('/api/notifications/',
                              {
                                  'type': Notification.TYPE_ATTENDANCE,
                              })
        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 1)

        for n in result:
            self.assertEqual(n['type'], Notification.TYPE_ATTENDANCE)

    def test_notification_get_list_filter_date(self):
        notification1 = Notification.objects.create(
            title='New test task 1',
            owner=self.user_owner,
            description='A difficult test task 1',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='Attendance',
            owner=self.user_owner,
            description='Your son did not attended classes today.',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=self.target_student,
            subject=self.lengua,
            type=Notification.TYPE_ATTENDANCE,
        )
        notification3 = Notification.objects.create(
            title='New test task 2',
            owner=self.user_owner,
            description='A difficult test task 2',
            date=datetime.datetime(2017, 8, 1, 1, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification4 = Notification.objects.create(
            title='New test task 5',
            owner=self.user_owner,
            description='A difficult test task 5',
            date=datetime.datetime(2017, 8, 2, 1, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification5 = Notification.objects.create(
            title='New test exam 3',
            owner=self.user_owner,
            description='A difficult test exam 3',
            date=datetime.datetime(2017, 8, 3, 1, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.ingles,
            type=Notification.TYPE_EXAM,
        )
        notification6 = Notification.objects.create(
            title='New test exam 6',
            owner=self.user_owner,
            description='A difficult test exam 3',
            date=datetime.datetime(2017, 8, 4, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.ingles,
            type=Notification.TYPE_EXAM,
        )

        factory = APIRequestFactory()

        #######################################################################
        fd = datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC)
        td = datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC)
        request = factory.get(
            '/api/notifications/',
            {
                'from_date': fd,
                'to_date': td,
            })

        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 2)

        for n in result:
            self.assertTrue(
                datetime.datetime.strptime(
                    n['date'], ISO_DATE_FORMAT
                ).replace(tzinfo=pytz.UTC) >= fd and
                datetime.datetime.strptime(
                    n['date'], ISO_DATE_FORMAT
                ).replace(tzinfo=pytz.UTC) <= td)

        #######################################################################
        fd = datetime.datetime(2017, 8, 3, 0, 0, 0, 0, pytz.UTC)
        td = datetime.datetime(2017, 8, 4, 0, 0, 0, 0, pytz.UTC)
        request = factory.get(
            '/api/notifications/',
            {
                'from_date': fd,
                'to_date': td,
            })

        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 1)

        for n in result:
            self.assertTrue(
                datetime.datetime.strptime(
                    n['date'], ISO_DATE_FORMAT
                ).replace(tzinfo=pytz.UTC) >= fd and
                datetime.datetime.strptime(
                    n['date'], ISO_DATE_FORMAT
                ).replace(tzinfo=pytz.UTC) <= td)

    def test_notification_get_list_size(self):
        notification1 = Notification.objects.create(
            title='New test task 1',
            owner=self.user_owner,
            description='A difficult test task 1',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification2 = Notification.objects.create(
            title='Attendance',
            owner=self.user_owner,
            description='Your son did not attended classes today.',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=self.target_student,
            subject=self.lengua,
            type=Notification.TYPE_ATTENDANCE,
        )
        notification3 = Notification.objects.create(
            title='New test task 2',
            owner=self.user_owner,
            description='A difficult test task 2',
            date=datetime.datetime(2017, 8, 1, 1, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification4 = Notification.objects.create(
            title='New test task 5',
            owner=self.user_owner,
            description='A difficult test task 5',
            date=datetime.datetime(2017, 8, 2, 1, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            subject=self.mates,
            type=Notification.TYPE_TASK,
        )
        notification5 = Notification.objects.create(
            title='New test exam 3',
            owner=self.user_owner,
            description='A difficult test exam 3',
            date=datetime.datetime(2017, 8, 3, 1, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.ingles,
            type=Notification.TYPE_EXAM,
        )
        notification6 = Notification.objects.create(
            title='New test exam 6',
            owner=self.user_owner,
            description='A difficult test exam 3',
            date=datetime.datetime(2017, 8, 4, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            subject=self.ingles,
            type=Notification.TYPE_EXAM,
        )

        factory = APIRequestFactory()

        #######################################################################
        for i in range(7):
            request = factory.get(
                '/api/notifications/',
                {
                    'size': i,
                })

            force_authenticate(request, user=self.parent_target_student)
            view = NotificationsService.as_view({'get': 'list'})
            response = view(request)

            self.assertEqual(response.status_code, 200)

            result = response.data

            self.assertEqual(len(result), i)

        #######################################################################
        request = factory.get(
            '/api/notifications/',
            {
                'size': 100,
            })

        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 6)

    def test_notification_post_unauthorized(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/', {})

        view = NotificationsService.as_view({'post': 'create'})

        response = view(request)

        self.assertEqual(response.status_code, 401)

    def test_notification_post_no_target(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/',
                               {
                                   'title': 'New task',
                                   'owner': 1,
                                   'description': 'A difficult task',
                                   'date': datetime.datetime(2017, 7, 27),
                                   # 'target_class_id': None,
                                   # 'target_student_id': None,
                                   'icon': 'test',
                                })
        force_authenticate(request, user=self.user_owner)

        view = NotificationsService.as_view({'post': 'create'})

        response = view(request)

        self.assertEqual(response.status_code, 400)

    def test_notification_post_two_target(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/',
                               {
                                   'title': 'New task',
                                   'description': 'A difficult task',
                                   'date': datetime.datetime(2017, 7, 27),
                                   'target_class_id': self.target_class.id,
                                   'target_student_id': self.target_student.id,
                                   'icon': 'test',
                                })
        force_authenticate(request, user=self.user_owner)

        view = NotificationsService.as_view({'post': 'create'})

        response = view(request)

        self.assertEqual(response.status_code, 201)

        notification = Notification.objects.filter(title='New task').first()

        self.assertIsNotNone(notification)

        self.assertEqual(notification.owner.email, 'mates@school.com')
        self.assertEqual(
            notification.target_student.email, 'cristobal@school.com')
        self.assertEqual(notification.target_class.name, '1B')
        self.assertEqual(notification.title, 'New task')
        self.assertEqual(notification.description, 'A difficult task')
        self.assertEqual(notification.date.year, 2017)
        self.assertEqual(notification.date.month, 7)
        self.assertEqual(notification.date.day, 27)
        self.assertEqual(notification.icon, 'test')

    def test_notification_post_to_user(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/',
                               {
                                   'title': 'New task',
                                   'owner': self.user_owner.id,
                                   'description': 'A difficult task',
                                   'date': datetime.datetime(2017, 7, 27),
                                   'target_class_id': None,
                                   'target_student_id': self.target_student.id,
                                   'icon': 'test',
                                })
        force_authenticate(request, user=self.user_owner)

        view = NotificationsService.as_view({'post': 'create'})

        with mock.patch('worker.tasks.push_notification.delay') \
        as push_notification:
            response = view(request)

            self.assertTrue(push_notification.called_once_with(1))

        self.assertEqual(response.status_code, 201)

        notification = Notification.objects.filter(title='New task').first()

        self.assertIsNotNone(notification)

        self.assertEqual(notification.owner.email, 'mates@school.com')
        self.assertEqual(
            notification.target_student.email, 'cristobal@school.com')
        self.assertIsNone(notification.target_class)
        self.assertEqual(notification.title, 'New task')
        self.assertEqual(notification.description, 'A difficult task')
        self.assertEqual(notification.date.year, 2017)
        self.assertEqual(notification.date.month, 7)
        self.assertEqual(notification.date.day, 27)
        self.assertEqual(notification.icon, 'test')

        # self.fail('Test incomplete')

    def test_notification_post_to_class(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/',
                               {
                                   'title': 'New task',
                                   'owner': self.user_owner.id,
                                   'description': 'A difficult task',
                                   'date': datetime.datetime(2017, 7, 27),
                                   'target_class_id': self.target_class.id,
                                   'target_student_id': None,
                                   'icon': 'test',
                                })
        force_authenticate(request, user=self.user_owner)

        view = NotificationsService.as_view({'post': 'create'})

        response = view(request)

        self.assertEqual(response.status_code, 201)

        notification = Notification.objects.filter(title='New task').first()

        self.assertIsNotNone(notification)

        self.assertEqual(notification.owner.email, 'mates@school.com')
        self.assertIsNone(notification.target_student)
        self.assertEqual(notification.target_class.name, '1B')
        self.assertEqual(notification.title, 'New task')
        self.assertEqual(notification.description, 'A difficult task')
        self.assertEqual(notification.date.year, 2017)
        self.assertEqual(notification.date.month, 7)
        self.assertEqual(notification.date.day, 27)
        self.assertEqual(notification.icon, 'test')

        # self.fail('Test incomplete')

    def test_notification_post_json(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/',
                               {
                                   'title': 'New task',
                                   'description': 'A difficult task',
                                   'date': datetime.datetime(2017, 7, 27),
                                   'target_class_id': self.target_class.id,
                                   'target_student_id': self.target_student.id,
                                   'icon': 'test',
                                   'custom_fields': {'test': 'test value'},
                                })
        force_authenticate(request, user=self.user_owner)

        view = NotificationsService.as_view({'post': 'create'})

        response = view(request)

        # response.render()
        # print(response.content)

        self.assertEqual(response.status_code, 201)

        notification = Notification.objects.filter(title='New task').first()

        self.assertIsNotNone(notification)

        self.assertEqual(notification.custom_fields, {'test': 'test value'})

    def test_notification_get_by_owner(self):
        notification = Notification.objects.create(
            title='New test task',
            owner=self.user_owner,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            icon='test',
        )

        factory = APIRequestFactory()
        request = factory.get('/api/notifications/')
        force_authenticate(request, user=self.user_owner)
        view = NotificationsService.as_view({'get': 'retrieve'})
        response = view(request, pk=notification.id)

        self.assertEqual(response.status_code, 200)

    def test_notification_get_by_target_student_parent(self):
        notification = Notification.objects.create(
            title='New test task',
            owner=self.user_owner,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            icon='test',
        )

        factory = APIRequestFactory()
        request = factory.get('/api/notifications/')
        force_authenticate(request, user=self.parent_target_student)
        view = NotificationsService.as_view({'get': 'retrieve'})
        response = view(request, pk=notification.id)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(result['title'], 'New test task')
        self.assertEqual(result['owner']['id'], self.user_owner.id)
        self.assertEqual(result['description'], 'A difficult test task')
        self.assertEqual(result['date'], '2017-08-01T00:00:00Z')
        self.assertEqual(result['target_class'], None)
        self.assertEqual(result['target_student']['id'], self.target_student.id)
        self.assertEqual(result['icon'], 'test')

    def test_notification_get_by_target_class(self):
        notification = Notification.objects.create(
            title='New test task',
            owner=self.user_owner,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            icon='test',
        )

        factory = APIRequestFactory()
        request = factory.get('/api/notifications/')
        force_authenticate(request, user=self.parent_target_student_class)
        view = NotificationsService.as_view({'get': 'retrieve'})
        response = view(request, pk=notification.id)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(result['title'], 'New test task')
        self.assertEqual(result['owner']['id'], self.user_owner.id)
        self.assertEqual(result['description'], 'A difficult test task')
        self.assertEqual(result['date'], '2017-08-01T00:00:00Z')
        self.assertEqual(result['target_class']['id'], self.target_class.id)
        self.assertEqual(result['target_student'], None)
        self.assertEqual(result['icon'], 'test')

    def test_notification_get_by_target_student_unauthorized(self):
        notification = Notification.objects.create(
            title='New test task',
            owner=self.user_owner,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            icon='test',
        )

        factory = APIRequestFactory()
        request = factory.get('/api/notifications/')
        force_authenticate(request, user=self.other_user)
        view = NotificationsService.as_view({'get': 'retrieve'})
        response = view(request, pk=notification.id)

        self.assertEqual(response.status_code, 404)

    def test_notification_get_by_target_class_unauthorized(self):
        notification = Notification.objects.create(
            title='New test task',
            owner=self.user_owner,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            icon='test',
        )

        factory = APIRequestFactory()
        request = factory.get('/api/notifications/')
        force_authenticate(request, user=self.other_user)
        view = NotificationsService.as_view({'get': 'retrieve'})
        response = view(request, pk=notification.id)

        self.assertEqual(response.status_code, 404)

    def test_notification_get_list_owner(self):
        n1 = Notification.objects.create(
            title='New test task',
            owner=self.user_owner,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student_class,
            type=Notification.TYPE_EXAM,
            custom_fields={ 'score': 9.5 },
            icon='test1',
        )
        n2 = Notification.objects.create(
            title='New test task 2',
            owner=self.user_owner,
            description='A difficult test task 2',
            date=datetime.datetime(2017, 8, 2, 0, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
            icon='test2',
        )
        n3 = Notification.objects.create(
            title='New test task 3',
            owner=self.other_user,
            description='A difficult test task 3',
            date=datetime.datetime(2017, 8, 3, 0, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.target_student,
            icon='test3',
        )

        factory = APIRequestFactory()
        request = factory.get('/api/notifications_received/')
        force_authenticate(request, user=self.parent_target_student_class)
        view = NotificationsService.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(len(result), 2)

        self.assertEqual(result[0]['id'], n2.id)
        self.assertEqual(result[0]['title'], 'New test task 2')
        self.assertEqual(result[0]['owner']['id'], self.user_owner.id)
        self.assertEqual(result[0]['description'], 'A difficult test task 2')
        self.assertEqual(result[0]['date'], '2017-08-02T00:00:00Z')
        self.assertEqual(result[0]['target_class']['id'], self.target_class.id)
        self.assertEqual(result[0]['target_student'], None)
        self.assertEqual(result[0]['icon'], 'test2')
        self.assertEqual(result[1]['id'], n1.id)
        self.assertEqual(result[1]['title'], 'New test task')
        self.assertEqual(result[1]['owner']['id'], self.user_owner.id)
        self.assertEqual(result[1]['description'], 'A difficult test task')
        self.assertEqual(result[1]['date'], '2017-08-01T00:00:00Z')
        self.assertEqual(result[1]['target_class'], None)
        self.assertEqual(result[1]['target_student']['id'],
                         self.target_student_class.id)
        self.assertEqual(result[1]['type'], Notification.TYPE_EXAM)
        self.assertEqual(result[1]['custom_fields'], {'score': 9.5})
        self.assertEqual(result[1]['icon'], 'test1')

    def test_notification_post_bad_subject(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/',
                               {
                                   'title': 'New task',
                                   'owner': 1,
                                   'description': 'A difficult task',
                                   'date': datetime.datetime(2017, 7, 27),
                                   'target_class': self.target_class.id,
                                   # 'target_student': None,
                                   'icon': 'test',
                                   'subject_id': 'bad',
                                })
        force_authenticate(request, user=self.user_owner)

        view = NotificationsService.as_view({'post': 'create'})

        response = view(request)

        self.assertEqual(response.status_code, 400)

    def test_notification_post_with_subject(self):
        factory = APIRequestFactory()
        request = factory.post('/api/notifications/',
                               {
                                   'title': 'New task',
                                   'owner': self.user_owner.id,
                                   'description': 'A difficult task',
                                   'date': datetime.datetime(2017, 7, 27),
                                   'target_class_id': self.target_class.id,
                                   'target_student_id': None,
                                   'icon': 'test',
                                   'subject_id': self.lengua.id,
                                })
        force_authenticate(request, user=self.user_owner)

        view = NotificationsService.as_view({'post': 'create'})

        response = view(request)

        response.render()
        # print(response.content)

        self.assertEqual(response.status_code, 201)

        notification = Notification.objects.filter(title='New task').first()

        self.assertIsNotNone(notification)

        self.assertEqual(notification.owner.email, 'mates@school.com')
        self.assertIsNone(notification.target_student)
        self.assertEqual(notification.target_class.name, '1B')
        self.assertEqual(notification.title, 'New task')
        self.assertEqual(notification.description, 'A difficult task')
        self.assertEqual(notification.date.year, 2017)
        self.assertEqual(notification.date.month, 7)
        self.assertEqual(notification.date.day, 27)
        self.assertEqual(notification.icon, 'test')
        self.assertEqual(notification.subject, self.lengua)


class ClassTest(TestCase):

    def setUp(self):
        from core.management.commands.initadmin import (insert_data_for_tests,
                                                        init_database)
        init_database()
        insert_data_for_tests()

        self.user_admin = User.objects.get(email='team@cathedralsw.com')
        self.sample_class = Class.objects.get(name='1B')

    def test_class_route(self):
        found = resolve('/api/classes/')

        # self.assertEqual(found.func, ClassesService.as_view({'get': 'list'}))

    def test_class_get_list_unathorize(self):
        factory = APIRequestFactory()
        request = factory.get('/api/classes/', {})

        view = ClassesService.as_view({'get': 'list'})

        response = view(request)

        self.assertEqual(response.status_code, 401)

    def test_class_get_list(self):
        factory = APIRequestFactory()
        request = factory.get('/api/classes/', {})

        view = ClassesService.as_view({'get': 'list'})

        force_authenticate(request, user=self.user_admin)
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = sorted(response.data,
                        key=lambda c: c['name'])

        self.assertEqual(len(result), 3)

        self.assertEqual(result[0]['name'], '1A')
        self.assertEqual(len(result[0]['teachers_subjects']), 4)

        self.assertEqual(len(result[0]['students']), 2)
        students = [s['first_name'] for s in result[0]['students']]
        self.assertTrue('Javier' in students)
        self.assertTrue('Alexis' in students)

        teachers = [s['teacher']['first_name']
                    for s in result[0]['teachers_subjects']]
        self.assertTrue('Profe mates' in teachers)
        self.assertTrue('Profe lengua' in teachers)
        self.assertTrue('Profe inglés y ciencias sociales' in teachers)

        self.assertEqual(result[1]['name'], '1B')
        self.assertEqual(len(result[1]['teachers_subjects']), 3)

        self.assertEqual(len(result[1]['students']), 2)
        students = [s['first_name'] for s in result[1]['students']]
        self.assertTrue('Cristóbal' in students)
        self.assertTrue('Belén' in students)

        teachers = [s['teacher']['first_name']
                    for s in result[1]['teachers_subjects']]
        self.assertTrue('Profe mates' in teachers)
        self.assertTrue('Profe lengua' in teachers)

        self.assertEqual(result[2]['name'], '2A')
        self.assertEqual(len(result[2]['teachers_subjects']), 3)

        self.assertEqual(len(result[2]['students']), 1)
        students = [s['first_name'] for s in result[2]['students']]
        self.assertTrue('Alexis 2' in students)

        teachers = [s['teacher']['first_name']
                    for s in result[2]['teachers_subjects']]
        self.assertTrue('Profe mates' in teachers)
        self.assertTrue('Profe lengua' in teachers)

    def test_class_get_class(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'mates@school.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/classes/{}/'.format(self.sample_class.id),
            {},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        the_class = response.json()

    # def test_class_get_class_students(self):
    #     c = Client()
    #     r1 = c.post(
    #         '/api/auth/',
    #         {
    #             'email': 'mates@school.com',
    #             'password': 'password123',
    #         }
    #     )

    #     response = c.get(
    #         '/api/classes/{}/students/'.format(self.sample_class.id),
    #         {},
    #         HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
    #     )
    #     self.assertEqual(response.status_code, 200)

    #     students = response.json()

    #     self.assertEqual(len(students), 2)


class UserTest(TestCase):

    def setUp(self):
        # create_default_groups()

        # group_students = Group.objects.get(name=GROUP_STUDENT_ID)

        # self.user_admin = User.objects.create_user(
        #     email='juan@mail.com',
        #     password='password123',
        # )

        # self.student1 = User.objects.create_user(
        #     email='maria@mail.com',
        #     password='qwerty321',
        # )
        # self.student1.groups.add(group_students)

        # self.student2 = User.objects.create_user(
        #     email='ernesto@mail.com',
        #     password='qwerty321',
        # )
        # self.student2.groups.add(group_students)

        from core.management.commands.initadmin import (insert_data_for_tests,
                                                        init_database)
        init_database()
        insert_data_for_tests()

        self.user = User.objects.get(email='cristobal.padre@school.com')
        self.teacher = User.objects.get(email='ingles.sociales@school.com')
        self.parent = User.objects.get(email='alexis.padre@school.com')
        self.student1 = User.objects.get(email='cristobal@school.com')
        self.student2 = User.objects.get(email='belen@school.com')
        # self.target_class = Class.objects.get(name='1B')

        self.student3 = User.objects.get(email='alexis@school.com')
        self.student4 = User.objects.get(email='javier@school.com')

    def test_user_route(self):
        found = resolve('/api/users/')

        # self.assertEqual(found.func, ClassesService.as_view({'get': 'list'}))

    def test_user_get_list_unathorize(self):
        factory = APIRequestFactory()
        request = factory.get('/api/users/', {})

        view = UsersService.as_view({'get': 'list'})

        response = view(request)

        self.assertEqual(response.status_code, 401)

    def test_user_get_list_from_parent(self):
        factory = APIRequestFactory()
        request = factory.get('/api/users/', {})

        view = UsersService.as_view({'get': 'list'})

        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        # Cristóbal madre
        # Belén padre
        # Belén madre
        # Belén
        # Profesor mates
        # Profesor lengua
        # Profesor sociales
        self.assertEqual(len(result), 7)

        self.assertTrue('id' in result[0])
        self.assertTrue('first_name' in result[0])
        self.assertTrue('last_name' in result[0])
        self.assertTrue('groups' in result[0])
        self.assertTrue('email' not in result[0])

    def test_user_get_list_from_parent_filter_no_students(self):
        factory = APIRequestFactory()
        request = factory.get('/api/users/',
                              {
                                  'no_students': 'True',
                              })

        view = UsersService.as_view({'get': 'list'})

        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        # Cristóbal madre
        # Belén padre
        # Belén madre
        # Profesor mates
        # Profesor lengua
        # Profesor sociales
        self.assertEqual(len(result), 6)

        for r in result:
            self.assertTrue(r['id'] != self.student2.id)
            self.assertTrue('id' in r)
            self.assertTrue('first_name' in r)
            self.assertTrue('last_name' in r)
            self.assertTrue('groups' in r)
            self.assertTrue('email' not in r)

    def test_user_get_list_from_teacher(self):
        factory = APIRequestFactory()
        request = factory.get('/api/users/', {})

        view = UsersService.as_view({'get': 'list'})

        force_authenticate(request, user=self.teacher)
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        # Profesor mates
        # Profesor lengua
        # Alexis madre
        # Alexis padre
        # Alexis
        # Alexis 2
        # Javier padre
        # Javier madre
        # Javier
        # Belén madre
        # Belén padre
        # Belén
        # Cristóbal madre
        # Cristóbal padre
        # Cristóbal
        self.assertEqual(len(result), 15)

        self.assertTrue('id' in result[0])
        self.assertTrue('first_name' in result[0])
        self.assertTrue('last_name' in result[0])
        self.assertTrue('groups' in result[0])
        self.assertTrue('email' not in result[0])

    def test_user_get_list_from_teacher_filter_no_students(self):
        factory = APIRequestFactory()
        request = factory.get('/api/users/',
                              {
                                  'no_students': 'True',
                              })

        view = UsersService.as_view({'get': 'list'})

        force_authenticate(request, user=self.teacher)
        response = view(request)

        self.assertEqual(response.status_code, 200)

        result = response.data

        # Profesor mates
        # Profesor lengua
        # Alexis madre
        # Alexis padre
        # Javier padre
        # Javier madre
        # Belén madre
        # Belén padre
        # Cristóbal padre
        # Cristóbal madre
        self.assertEqual(len(result), 10)

        for r in result:
            self.assertTrue(r['id'] != self.student3.id)
            self.assertTrue(r['id'] != self.student4.id)
            self.assertTrue('id' in r)
            self.assertTrue('first_name' in r)
            self.assertTrue('last_name' in r)
            self.assertTrue('groups' in r)
            self.assertTrue('email' not in r)

    def test_user_get_one(self):
        factory = APIRequestFactory()
        request = factory.get('/api/users/', {})

        view = UsersService.as_view({'get': 'retrieve'})

        force_authenticate(request, user=self.user)
        response = view(request, pk=self.parent.id)

        self.assertEqual(response.status_code, 200)

        result = response.data

        self.assertEqual(result['id'], self.parent.id)
        self.assertEqual(result['first_name'], self.parent.first_name)
        self.assertEqual(result['last_name'], self.parent.last_name)
        self.assertTrue('groups' in result)
        self.assertTrue('email' not in result)
        self.assertTrue('children' in result)
        self.assertEqual(len(result['children']), 2)


class SubjectsServiceTest(TestCase):

    def setUp(self):
        from core.management.commands.initadmin import (insert_data_for_tests,
                                                        init_database)
        init_database()
        insert_data_for_tests()

        # self.user = User.objects.get(email='cristobal.padre@school.com')
        # self.teacher = User.objects.get(email='ingles.sociales@school.com')
        # self.parent = User.objects.get(email='alexis.padre@school.com')
        # self.student1 = User.objects.get(email='cristobal@school.com')
        # self.student2 = User.objects.get(email='belen@school.com')
        # self.student3 = User.objects.get(email='alexis@school.com')
        # self.student4 = User.objects.get(email='javier@school.com')
        self.target_class = Class.objects.get(name='1B')
        self.sociales = Subject.objects.get(name='Ciencias sociales')

    def test_subjects_route(self):
        found = resolve('/api/subjects/')

        # self.assertEqual(found.func, ClassesService.as_view({'get': 'list'}))

    def test_subjects_get(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'ingles.sociales@school.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/subjects/',
            {},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )

        self.assertEqual(response.status_code, 200)

        subjects = response.json()

        self.assertEqual(len(subjects), 2)

    def test_subjects_get_filter_class(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'ingles.sociales@school.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/subjects/',
            {
                "class": self.target_class.id
            },
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )

        self.assertEqual(response.status_code, 200)

        subjects = response.json()

        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0]['id'], self.sociales.id)


class ChatServiceTest(TestCase):

    def setUp(self):
        a = User.objects.create_user(
            email='a@m.com',
            password='password123',
        )
        self.user_a = a.id

        b = User.objects.create_user(
            email='b@m.com',
            password='password123',
        )
        self.user_b = b.id

        c = User.objects.create_user(
            email='c@m.com',
            password='password123',
        )
        self.user_c = c.id

        d = User.objects.create_user(
            email='d@m.com',
            password='password123',
        )
        self.user_d = d.id

        self.client = client
        self.client.drop_database('test_chats_history')
        self.db = self.client['test_chats_history']

        chat_history = [
            {
                'user_from': a.id,
                'user_to': b.id,
                'conversation_id': '{}-{}'.format(
                    min(a.id, b.id), max(a.id, b.id)),
                'message': 'hola!',
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 0, 0,
                                               pytz.UTC),
            },
            {
                'user_from': a.id,
                'user_to': b.id,
                'conversation_id': '{}-{}'.format(
                    min(a.id, b.id), max(a.id, b.id)),
                'message': ':)',
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 1, 0,
                                               pytz.UTC),
            },
            {
                'user_from': c.id,
                'user_to': d.id,
                'conversation_id': '{}-{}'.format(
                    min(c.id, d.id), max(c.id, d.id)),
                'message': 'hello!',
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 1, 0,
                                               pytz.UTC),
            },
            {
                'user_from': b.id,
                'user_to': a.id,
                'conversation_id': '{}-{}'.format(
                    min(a.id, b.id), max(a.id, b.id)),
                'message': 'hey!',
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 2, 0,
                                               pytz.UTC),
            },
            {
                'user_from': c.id,
                'user_to': a.id,
                'conversation_id': '{}-{}'.format(
                    min(a.id, c.id), max(a.id, c.id)),
                'message': 'buenas!',
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 3, 0,
                                               pytz.UTC),
            },
        ]

        col = self.db.chats_history
        # col.insert_many(chat_history)
        for m in chat_history:
            col.insert(m)

    def tearDown(self):
        self.client.drop_database('test_chats_history')

    def test_chats_route(self):
        found = resolve('/api/chats/')

        # self.assertEqual(found.func, )

    def test_chats_get_forbidden(self):
        c = Client()

        response = c.get(
            '/api/chats/',
            {},
            # HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_chats_get(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'a@m.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/chats/',
            {},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        chats = response.json()

        self.assertEqual(len(chats), 2)
        self.assertEqual(chats[1]['user']['id'], self.user_b)
        self.assertEqual(chats[1]['last_user_from']['id'], self.user_b)
        self.assertEqual(chats[1]['last_message'], 'hey!')
        self.assertEqual(chats[1]['timestamp'], '2017-08-01T00:00:02')
        self.assertEqual(chats[0]['user']['id'], self.user_c)
        self.assertEqual(chats[0]['last_user_from']['id'], self.user_c)
        self.assertEqual(chats[0]['last_message'], 'buenas!')
        self.assertEqual(chats[0]['timestamp'], '2017-08-01T00:00:03')

    def test_chat_history_route(self):
        found = resolve('/api/chats/{}/'.format(self.user_b))

        # self.assertEqual(found.func, )

    def test_chat_history_get_forbidden(self):
        c = Client()

        response = c.get(
            '/api/chats/{}/'.format(self.user_b),
            {},
            # HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_chats_history_get(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'a@m.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/chats/{}/'.format(self.user_b),
            {},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        messages = response.json()

        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[2]['user_from']['id'], self.user_a)
        self.assertEqual(messages[2]['user_to']['id'], self.user_b)
        self.assertEqual(messages[2]['message'], 'hola!')
        self.assertEqual(messages[2]['timestamp'], '2017-08-01T00:00:00')
        self.assertEqual(messages[1]['user_from']['id'], self.user_a)
        self.assertEqual(messages[1]['user_to']['id'], self.user_b)
        self.assertEqual(messages[1]['message'], ':)')
        self.assertEqual(messages[1]['timestamp'], '2017-08-01T00:00:01')
        self.assertEqual(messages[0]['user_from']['id'], self.user_b)
        self.assertEqual(messages[0]['user_to']['id'], self.user_a)
        self.assertEqual(messages[0]['message'], 'hey!')
        self.assertEqual(messages[0]['timestamp'], '2017-08-01T00:00:02')

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_chats_history_get_size(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'a@m.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/chats/{}/'.format(self.user_b),
            {'size': 1},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        messages = response.json()

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['user_from']['id'], self.user_b)
        self.assertEqual(messages[0]['user_to']['id'], self.user_a)
        self.assertEqual(messages[0]['message'], 'hey!')
        self.assertEqual(messages[0]['timestamp'], '2017-08-01T00:00:02')

        response = c.get(
            '/api/chats/{}/'.format(self.user_b),
            {'size': 2},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        messages = response.json()

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]['user_from']['id'], self.user_a)
        self.assertEqual(messages[1]['user_to']['id'], self.user_b)
        self.assertEqual(messages[1]['message'], ':)')
        self.assertEqual(messages[1]['timestamp'], '2017-08-01T00:00:01')
        self.assertEqual(messages[0]['user_from']['id'], self.user_b)
        self.assertEqual(messages[0]['user_to']['id'], self.user_a)
        self.assertEqual(messages[0]['message'], 'hey!')
        self.assertEqual(messages[0]['timestamp'], '2017-08-01T00:00:02')

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_chats_history_get_from(self):
        c = Client()
        r1 = c.post(
            '/api/auth/',
            {
                'email': 'a@m.com',
                'password': 'password123',
            }
        )

        response = c.get(
            '/api/chats/{}/'.format(self.user_b),
            {'size': 1},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )

        response = c.get(
            '/api/chats/{}/'.format(self.user_b),
            {'size': 1, 'from': response.json()[-1]['id']},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        messages = response.json()

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['user_from']['id'], self.user_a)
        self.assertEqual(messages[0]['user_to']['id'], self.user_b)
        self.assertEqual(messages[0]['message'], ':)')
        self.assertEqual(messages[0]['timestamp'], '2017-08-01T00:00:01')

        response = c.get(
            '/api/chats/{}/'.format(self.user_b),
            {'size': 1, 'from': messages[-1]['id']},
            HTTP_AUTHORIZATION='JWT {}'.format(r1.json()['token'])
        )
        self.assertEqual(response.status_code, 200)

        messages = response.json()

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['user_from']['id'], self.user_a)
        self.assertEqual(messages[0]['user_to']['id'], self.user_b)
        self.assertEqual(messages[0]['message'], 'hola!')
        self.assertEqual(messages[0]['timestamp'], '2017-08-01T00:00:00')

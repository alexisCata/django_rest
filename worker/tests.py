import pytz
import datetime
import unittest.mock as mock

from django.test import TestCase
from django.test.utils import override_settings

from core.models import User, Notification, Class

from .tasks import push_notification


class PushNotificationTest(TestCase):

    def setUp(self):
        from core.management.commands.initadmin import (insert_data_for_tests,
                                                        init_database)
        init_database()
        insert_data_for_tests()

        self.user = User.objects.get(email='ingles.sociales@school.com')
        self.parent1 = User.objects.get(email='cristobal.padre@school.com')
        self.parent2 = User.objects.get(email='cristobal.madre@school.com')
        self.parent3 = User.objects.get(email='belen.padre@school.com')
        self.parent4 = User.objects.get(email='belen.madre@school.com')
        self.student1 = User.objects.get(email='cristobal@school.com')
        # self.student2 = User.objects.get(email='belen@school.com')
        self.target_class = Class.objects.get(name='1B')

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        SCHOOL_WEBSOCKET_BACKEND_URL='http://111.111.111.111:8888/'
    )
    def test_push_notification_one_target(self):
        notification = Notification.objects.create(
            title='New test task',
            owner=self.user,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            timestamp=datetime.datetime(2017, 8, 1, 1, 0, 0, 0, pytz.UTC),
            target_class=None,
            target_student=self.student1,
        )

        with mock.patch('requests.get') as requests_get:
            push_notification(notification.id)

            ids = ','.join([str(id)
                            for id in sorted([
                                self.parent1.id,
                                self.parent2.id,
                            ])])

            self.assertTrue(requests_get.called)
            requests_get.assert_called_with(
                'http://111.111.111.111:8888/notification',
                params={
                    'id': notification.id,
                    'date': '2017-08-01 00:00:00',
                    'owner': self.user.id,
                    'target_student': str(self.student1.id),
                    'target_class': None,
                    'timestamp': '2017-08-01 01:00:00',
                    'title': 'New test task',
                    'description': 'A difficult test task',
                    'user': ids,
                }
            )

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        SCHOOL_WEBSOCKET_BACKEND_URL='http://111.111.111.111:8888/'
    )
    def test_push_notification_multiple_targets(self):
        notification = Notification.objects.create(
            title='New test task',
            owner=self.user,
            description='A difficult test task',
            date=datetime.datetime(2017, 8, 1, 0, 0, 0, 0, pytz.UTC),
            timestamp=datetime.datetime(2017, 8, 1, 1, 0, 0, 0, pytz.UTC),
            target_class=self.target_class,
            target_student=None,
        )

        with mock.patch('requests.get') as requests_get:
            push_notification(notification.id)

            ids = ','.join(
                [str(id)
                 for id in sorted([self.parent1.id,
                                   self.parent2.id,
                                   self.parent3.id,
                                   self.parent4.id,
                                   ]
                                  )
                 ]
            )

            self.assertTrue(requests_get.called)
            requests_get.assert_called_with(
                'http://111.111.111.111:8888/notification',
                params={
                    'id': notification.id,
                    'date': '2017-08-01 00:00:00',
                    'owner': self.user.id,
                    'target_student': None,
                    'target_class': self.target_class.id,
                    'timestamp': '2017-08-01 01:00:00',
                    'title': 'New test task',
                    'description': 'A difficult test task',
                    'user': ids,
                }
            )

import datetime
import pytz

from django.test import TestCase
from django.test.utils import override_settings

from core.models import User
from .database import client, get_chats, get_chat_history


class ChatsDatabase(TestCase):

    def setUp(self):
        from core.management.commands.initadmin import (insert_data_for_tests,
                                                        init_database)
        init_database()
        insert_data_for_tests()

        self.u1 = User.objects.get(email='lengua@school.com').id
        self.u2 = User.objects.get(email='ingles.sociales@school.com').id
        self.u3 = User.objects.get(email='alexis.padre@school.com').id
        self.u4 = User.objects.get(email='cristobal.padre@school.com').id

        self.client = client
        self.client.drop_database('test_chats_history')
        self.db = self.client['test_chats_history']

        chat_history = [
            {
                'user_from': self.u1,
                'user_to': self.u2,
                'conversation_id': '{}-{}'.format(self.u1, self.u2),
                'message': "hola!",
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 0, 0,
                                               pytz.UTC),
            },
            {
                'user_from': self.u1,
                'user_to': self.u2,
                'conversation_id': '{}-{}'.format(self.u1, self.u2),
                'message': ":)",
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 1, 0,
                                               pytz.UTC),
            },
            {
                'user_from': self.u3,
                'user_to': self.u4,
                'conversation_id': '{}-{}'.format(self.u3, self.u4),
                'message': "hello!",
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 1, 0,
                                               pytz.UTC),
            },
            {
                'user_from': self.u2,
                'user_to': self.u1,
                'conversation_id': '{}-{}'.format(self.u1, self.u2),
                'message': "hey!",
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 2, 0,
                                               pytz.UTC),
            },
            {
                'user_from': self.u1,
                'user_to': self.u3,
                'conversation_id': '{}-{}'.format(self.u1, self.u3),
                'message': "buenas!",
                'timestamp': datetime.datetime(2017, 8, 1, 0, 0, 3, 0,
                                               pytz.UTC),
            },
        ]

        col = self.db.chats_history
        col.insert_many(chat_history)

    def tearDown(self):
        self.client.drop_database('test_chats_history')

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_get_chats(self):
        messages = get_chats(self.u1)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]['user']['id'], self.u2)
        self.assertEqual(messages[1]['last_user_from']['id'], self.u2)
        self.assertEqual(messages[1]['last_message'], 'hey!')
        self.assertEqual(messages[1]['last_read'], None)
        self.assertEqual(messages[1]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))
        self.assertEqual(messages[0]['user']['id'], self.u3)
        self.assertEqual(messages[0]['last_user_from']['id'], self.u1)
        self.assertEqual(messages[0]['last_message'], 'buenas!')
        self.assertEqual(messages[0]['last_read'], None)
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 3, 0))

        messages = get_chats(self.u2)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['user']['id'], self.u1)
        self.assertEqual(messages[0]['last_user_from']['id'], self.u2)
        self.assertEqual(messages[0]['last_message'], 'hey!')
        self.assertEqual(messages[0]['last_read'], None)
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_get_chats_read(self):
        messages = get_chats(self.u1)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]['user']['id'], self.u2)
        self.assertEqual(messages[1]['last_user_from']['id'], self.u2)
        self.assertEqual(messages[1]['last_message'], 'hey!')
        self.assertEqual(messages[1]['last_read'], None)
        self.assertEqual(messages[1]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))
        self.assertEqual(messages[0]['user']['id'], self.u3)
        self.assertEqual(messages[0]['last_user_from']['id'], self.u1)
        self.assertEqual(messages[0]['last_message'], 'buenas!')
        self.assertEqual(messages[0]['last_read'], None)
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 3, 0))

        get_chat_history(self.u1, self.u2, mark_as_read=True)

        messages = get_chats(self.u1)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]['user']['id'], self.u2)
        self.assertEqual(messages[1]['last_user_from']['id'], self.u2)
        self.assertEqual(messages[1]['last_message'], 'hey!')
        self.assertEqual(messages[1]['last_read'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))
        self.assertEqual(messages[1]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))
        self.assertEqual(messages[0]['user']['id'], self.u3)
        self.assertEqual(messages[0]['last_user_from']['id'], self.u1)
        self.assertEqual(messages[0]['last_message'], 'buenas!')
        self.assertEqual(messages[0]['last_read'], None)
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 3, 0))

        get_chat_history(self.u1, self.u3, mark_as_read=True)

        messages = get_chats(self.u1)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]['user']['id'], self.u2)
        self.assertEqual(messages[1]['last_user_from']['id'], self.u2)
        self.assertEqual(messages[1]['last_message'], 'hey!')
        self.assertEqual(messages[1]['last_read'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))
        self.assertEqual(messages[1]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))
        self.assertEqual(messages[0]['user']['id'], self.u3)
        self.assertEqual(messages[0]['last_user_from']['id'], self.u1)
        self.assertEqual(messages[0]['last_message'], 'buenas!')
        self.assertEqual(messages[0]['last_read'],
                         datetime.datetime(2017, 8, 1, 0, 0, 3, 0))
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 3, 0))

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_get_chat_history(self):
        messages = get_chat_history(self.u1, self.u2)

        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[2]['user_from']['id'], self.u1)
        self.assertEqual(messages[2]['user_to']['id'], self.u2)
        self.assertEqual(messages[2]['message'], 'hola!')
        self.assertEqual(messages[2]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 0, 0))
        self.assertEqual(messages[1]['user_from']['id'], self.u1)
        self.assertEqual(messages[1]['user_to']['id'], self.u2)
        self.assertEqual(messages[1]['message'], ':)')
        self.assertEqual(messages[1]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 1, 0))
        self.assertEqual(messages[0]['user_from']['id'], self.u2)
        self.assertEqual(messages[0]['user_to']['id'], self.u1)
        self.assertEqual(messages[0]['message'], 'hey!')
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_get_chat_history_size(self):
        messages = get_chat_history(self.u1, self.u2, size=1)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['user_from']['id'], self.u2)
        self.assertEqual(messages[0]['user_to']['id'], self.u1)
        self.assertEqual(messages[0]['message'], 'hey!')
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))

        messages = get_chat_history(self.u1, self.u2, size=2)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]['user_from']['id'], self.u1)
        self.assertEqual(messages[1]['user_to']['id'], self.u2)
        self.assertEqual(messages[1]['message'], ':)')
        self.assertEqual(messages[1]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 1, 0))
        self.assertEqual(messages[0]['user_from']['id'], self.u2)
        self.assertEqual(messages[0]['user_to']['id'], self.u1)
        self.assertEqual(messages[0]['message'], 'hey!')
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 2, 0))

    @override_settings(
        MONGO_DATABASE = 'test_chats_history',
    )
    def test_get_chat_history_from(self):
        messages = get_chat_history(self.u1, self.u2, size=1)

        messages = get_chat_history(self.u1, self.u2, size=1,
                                    from_message=messages[0]['id'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['user_from']['id'], self.u1)
        self.assertEqual(messages[0]['user_to']['id'], self.u2)
        self.assertEqual(messages[0]['message'], ':)')
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 1, 0))

        messages = get_chat_history(self.u1, self.u2, size=1,
                                    from_message=messages[0]['id'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['user_from']['id'], self.u1)
        self.assertEqual(messages[0]['user_to']['id'], self.u2)
        self.assertEqual(messages[0]['message'], 'hola!')
        self.assertEqual(messages[0]['timestamp'],
                         datetime.datetime(2017, 8, 1, 0, 0, 0, 0))

from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth.models import Group

from .models import User, GROUP_PARENT_ID, create_default_groups


class UserTest(TestCase):
    """ Test module for User model """

    def setUp(self):
        create_default_groups()

    def test_user_create(self):
        user = User.objects.create_user(
            email='juan@mail.com',
            password='password123',
        )
        user.groups.add(Group.objects.get(name=GROUP_PARENT_ID))

        user = User.objects.get(email='juan@mail.com')

        # self.assertIsNotNone(user.profile)
        self.assertTrue(user.groups.filter(name=GROUP_PARENT_ID).exists())

    def test_user_unique_email(self):
        User.objects.create_user(
            email='juan@mail.com',
            password='password123',
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='juan@mail.com',
                password='password123',
            )

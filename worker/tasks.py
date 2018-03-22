from __future__ import absolute_import, unicode_literals
import requests

from django.conf import settings

from celery import shared_task

from core.models import Notification, User, GROUP_PARENT_ID


@shared_task
def push_notification(notification_id):
    notification = Notification.objects.get(id=notification_id)

    if notification.target_student:
        # Sorted for testing purposes
        ids = sorted([str(parent.id)
                      for parent in notification.target_student.parents.all()])

        requests.get(
            settings.SCHOOL_WEBSOCKET_BACKEND_URL + 'notification',
            params={
                'id': notification.id,
                'user': ','.join(ids),
                'owner': notification.owner.id,
                'title': notification.title,
                'description': notification.description,
                'timestamp': notification.timestamp.strftime(
                    '%Y-%m-%d %H:%M:%S'),
                'date': notification.date.strftime('%Y-%m-%d %H:%M:%S'),
                'target_class': notification.target_class.id \
                    if notification.target_class else None,
                # Not needed:
                'target_student': str(notification.target_student.id),
            })

    elif notification.target_class:
        # Sorted for testing purposes
        ids = [str(parent.id)
               for parent in User.objects.filter(
                   groups__name=GROUP_PARENT_ID,
                   children__attends=notification.target_class,
               ).order_by('id')]

        requests.get(
            settings.SCHOOL_WEBSOCKET_BACKEND_URL + 'notification',
            params={
                'id': notification.id,
                'user': ','.join(ids),
                'owner': notification.owner.id,
                'title': notification.title,
                'description': notification.description,
                'timestamp': notification.timestamp.strftime(
                    '%Y-%m-%d %H:%M:%S'),
                'date': notification.date.strftime('%Y-%m-%d %H:%M:%S'),
                'target_class': notification.target_class.id,
                'target_student': None,

            })

    else:
        raise Exception('notification without target student or target class')

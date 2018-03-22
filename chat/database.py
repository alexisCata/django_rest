from urllib.parse import quote_plus

from django.conf import settings

from bson import ObjectId
from pymongo import MongoClient, DESCENDING

from core.models import User


if settings.MONGO_USER:
    mongo_uri = 'mongodb://{}:{}@{}:{}'.format(
        quote_plus(settings.MONGO_USER),
        quote_plus(settings.MONGO_PASSWORD),
        settings.MONGO_HOST,
        settings.MONGO_PORT,
    )

else:
    mongo_uri = 'mongodb://{}:{}'.format(
        settings.MONGO_HOST,
        settings.MONGO_PORT,
    )

client = MongoClient(mongo_uri)


def get_chats(user_id):
    db = client[settings.MONGO_DATABASE]
    col = db.chats_history

    conversation_ids = list(col.find(
        {
            '$or': [
                {'user_from': user_id},
                {'user_to': user_id},
            ]
        },
        # sort=[('timestamp', DESCENDING)],
    ).distinct('conversation_id'))

    chats = []

    for id in conversation_ids:
        doc = col.find({'conversation_id': id},
                       sort=[('timestamp', DESCENDING)]).limit(1)[0]

        try:
            last_read_doc = col.find(
                {'conversation_id': id, 'read': True},
                sort=[('timestamp', DESCENDING)]
            ).limit(1)[0]

        except IndexError:
            last_read_doc = None

        user = User.objects.get(id=doc['user_from']
                                if doc['user_from'] != user_id
                                else doc['user_to'])
        user_from = User.objects.get(id=doc['user_from'])

        chats.append({
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'last_user_from': {
                'id': user_from.id,
                'first_name': user_from.first_name,
                'last_name': user_from.last_name
            },
            'last_message': doc['message'],
            'last_read': last_read_doc['timestamp'] if last_read_doc else None,
            'timestamp': doc['timestamp']
        })

    return sorted(chats,
                  key=lambda chat: chat['timestamp'],
                  reverse=True)


def get_chat_history(user1_id, user2_id, size=50, from_message=None,
                     mark_as_read=False):
    db = client[settings.MONGO_DATABASE]
    col = db.chats_history

    # conversation_id = '{}-{}'.format(
    #     min(user1_id, user2_id),
    #     max(user1_id, user2_id)
    # )

    if user1_id < user2_id:
        conversation_id = '{}-{}'.format(user1_id, user2_id)

    else:
        conversation_id = '{}-{}'.format(user2_id, user1_id)

    messages = []

    query = {
        'conversation_id': conversation_id
    }

    if from_message is not None:
        query['_id'] = {
            '$lt': ObjectId(from_message),
        }

    for message in col.find(
        query,
        sort=[('timestamp', DESCENDING)],
    ).limit(size):
        user_from = User.objects.get(id=message['user_from'])
        user_to = User.objects.get(id=message['user_to'])

        messages.append({
            'id': str(message['_id']),
            'user_from': {
                'id': user_from.id,
                'first_name': user_from.first_name,
                'last_name': user_from.last_name
            },
            'user_to': {
                'id': user_to.id,
                'first_name': user_to.first_name,
                'last_name': user_to.last_name
            },
            'message': message['message'],
            'timestamp': message['timestamp'],
            'read': message['read'] if 'read' in message else False,
        })

    if mark_as_read:
        col.update_many(
            query,
            {'$set': {'read': True}},
        )

    return messages

    # return list(col.find(
    #     {
    #         '$or': [
    #             {'user_from': user1_id, 'user_to': user2_id},
    #             {'user_from': user2_id, 'user_to': user1_id},
    #         ]
    #     },
    #     sort=[('timestamp', DESCENDING)],
    # ))

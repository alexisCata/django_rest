"""
$ export DJANGO_SETTINGS_MODULE=school.settings.production
"""

import os

from .defaults import *#


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_ENV_DB', 'postgres'),
        'USER': os.environ.get('DB_ENV_POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_ENV_POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_PORT_5432_TCP_ADDR', 'db'),
        'PORT': os.environ.get('DB_PORT_5432_TCP_PORT', ''),
    }
}


# MongoDB
MONGO_HOST = 'mongo'
MONGO_PORT = 27017
MONGO_DATABASE = 'chats_db'
MONGO_USER = os.environ.get('MONGO_INITDB_ROOT_USERNAME', '')
MONGO_PASSWORD = os.environ.get('MONGO_INITDB_ROOT_PASSWORD', '')


# Celery

# CELERY_BROKER_URL = "amqp://"
# CELERY_RESULT_BACKEND = "amqp://"

# CELERY_RESULT_BACKEND = 'redis://:password@host:port/db'
# CELERY_RESULT_BACKEND = 'redis://%s:%i' % (REDIS_HOST, REDIS_PORT)

RABBIT_HOSTNAME = os.environ.get('RABBIT_PORT_5672_TCP', 'rabbit')

if RABBIT_HOSTNAME.startswith('tcp://'):
    RABBIT_HOSTNAME = RABBIT_HOSTNAME.split('//')[1]

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', '')
if not CELERY_BROKER_URL:
    CELERY_BROKER_URL = 'amqp://{user}:{password}@{hostname}/{vhost}/'.format(
        user=os.environ.get('RABBIT_ENV_USER', 'admin'),
        password=os.environ.get('RABBIT_ENV_RABBITMQ_PASS', 'admin'),
        hostname=RABBIT_HOSTNAME,
        vhost=os.environ.get('RABBIT_ENV_VHOST', ''))

# Celery SQS backend

# BROKER_TRANSPORT = 'sqs'
# BROKER_TRANSPORT_OPTIONS = {
#     'region': AWS_REGION,
# }
#
# import urllib
# CELERY_BROKER_URL = 'sqs://{0}:{1}@'.format(
#     urllib.quote_plus(AWS_ACCESS_KEY_ID),
#     urllib.quote_plus(AWS_SECRET_ACCESS_KEY))


# Project configuration
SCHOOL_WEBSOCKET_BACKEND_URL = 'http://{}:{}/'.format(
    os.environ.get('WSHANDLER_PORT_8888_TCP_ADDR', 'wshandler'),
    os.environ.get('WSHANDLER_PORT_8888_TCP_PORT', '8888'),
)

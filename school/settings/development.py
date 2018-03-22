from .defaults import *


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, '..', 'db.sqlite3'),
    # }
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #     'NAME': 'postgres',
    #     'USER': 'postgres',
    #     'PASSWORD': 'postgres',
    #     'HOST': 'localhost',
    #     'PORT': 5432,
    # }
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'school',
        'USER': 'school',
        'PASSWORD': 'school',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}


# MongoDB
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DATABASE = 'chats_db'
MONGO_USER = ''
MONGO_PASSWORD = ''


# Project configuration
SCHOOL_WEBSOCKET_BACKEND_URL = 'http://192.168.1.42:8888/'

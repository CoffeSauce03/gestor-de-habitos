import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-vocedevetrocaraestachave-12345'
DEBUG = True
ALLOWED_HOSTS = ['*'] 

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dados', # O nosso app!
]

MIDDLEWARE = []
ROOT_URLCONF = 'config.urls'
TEMPLATES = [] 
WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent / 'db.sqlite3', # Guarda a DB na pasta principal
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
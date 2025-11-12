import os
from pathlib import Path

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Chave secreta (pode ser qualquer coisa para este projeto)
SECRET_KEY = 'django-insecure-o-importante-e-ter-uma-chave-aqui'

# A ÚNICA APLICAÇÃO QUE PRECISAMOS É A NOSSA
INSTALLED_APPS = [
    'dados', 
]

# Configuração do banco de dados (está correto)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent / 'db.sqlite3', # Guarda a DB na pasta principal
    }
}

# Configuração de Fuso Horário (Boa prática)
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
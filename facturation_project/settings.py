"""
Django settings for facturation_project project.
"""

from pathlib import Path

# Path racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent


# Paramètres de sécurité pour le développement
SECRET_KEY = 'django-insecure-_g0=0m1st71ii59fq2-i&3&kc+kq!v&##2vh2lwkla8y^j=26)'

DEBUG = True

ALLOWED_HOSTS = []


# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Vos applications
    'accounts',
    'dashboard',
    'documents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'facturation_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # dossier 'templates' racine pour base.html
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'facturation_project.wsgi.application'


# Base de données (SQLite en local)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalisation (Passage en français)
LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Libreville'

USE_I18N = True

USE_TZ = True


# Fichiers Statiques (CSS, JS)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Fichiers Médias (Fichiers temporaires Word et PDF générés)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Redirections Authentification
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_index'
LOGOUT_REDIRECT_URL = 'login'


# Configuration Email
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
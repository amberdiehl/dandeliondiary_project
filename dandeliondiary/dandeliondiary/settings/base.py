"""
Django settings for dandeliondiary project.
See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

SECRET_KEY = 'secret_key'
GOOGLE_API_KEY = 'api_key'

# General security settings
ALLOWED_HOSTS = ['www.dandeliondiary.com',]
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True  # prevent reading via javascript
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True  # prevent reading via javascript
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SECURE_SSL_REDIRECT = True  # allow access via https only
SECURE_CONTENT_TYPE_NOSNIFF = True  # force browser to always use the type provided in the Content-Type header
SECURE_BROWSER_XSS_FILTER = True  # enable browsers to block content that appears to be an XSS attack

# Default database definition
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dandeliondiary',
        'USER': 'user',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'guardian',
    'storages',
    'django_q',
    'bootstrap3',
    'account',
    'core',
    'household',
    'capture',
    'compare',
    'contribute',
    'forums',
    'public',
    'avatar',
]

SITE_ID = 1
WSGI_APPLICATION = 'dandeliondiary.wsgi.application'

# This is the proper way to do this in Django 1.10 but am using MIDDLEWARE_CLASSES below until account package is fixed.
#MIDDLEWARE = [
#    'django.middleware.security.SecurityMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
#    'django.middleware.clickjacking.XFrameOptionsMiddleware',
#    'account.middleware.LocaleMiddleware',
#    'account.middleware.TimezoneMiddleware',
#]

# Used for package "Account"; this is deprecated in Django 1.10 and will need to change soon.
MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    #'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'account.middleware.LocaleMiddleware',
    'account.middleware.TimezoneMiddleware',
]

ROOT_URLCONF = 'dandeliondiary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, '..', 'household/templates/household'),
            os.path.join(BASE_DIR, '..', 'capture/templates/capture'),
            os.path.join(BASE_DIR, '..', 'compare/templates/compare'),
            os.path.join(BASE_DIR, '..', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'account.context_processors.account',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
)

GUARDIAN_RENDER_403 = True


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Account application settings
ACCOUNT_SIGNUP_REDIRECT_URL = "household:household_dashboard"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "household:household_dashboard"
ACCOUNT_LOGIN_REDIRECT_URL = "compare:compare_dashboard"
ACCOUNT_LOGOUT_REDIRECT_URL = "public:home"
ACCOUNT_PASSWORD_CHANGE_REDIRECT_URL = "household:my_info"
ACCOUNT_EMAIL_UNIQUE = True
ACCOUNT_EMAIL_CONFIRMATION_REQUIRED = False
ACCOUNT_EMAIL_CONFIRMATION_EMAIL = True
ACCOUNT_USE_AUTH_AUTHENTICATE = False

# Avatar application settings
AVATAR_AUTO_GENERATE_SIZES = (80, 64, 50,)
AVATAR_DEFAULT_SIZE = 64
AVATAR_GRAVATAR_BACKUP = False
AVATAR_CHANGE_TEMPLATE = "avatar/avatar.html"

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

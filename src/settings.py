import os
import sys

from pathlib import Path
from django.templatetags.static import static
import environ
env = environ.Env()

env = environ.Env(DEBUG=(bool, True),REGISTRO=(bool, True))
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(os.path.join(BASE_DIR, 'libs'))

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# False if not in os.environ because of casting above
DEBUG = env('DEBUG')
NOMBRE= env('NOMBRE')
LOGO= env('LOGO')
LOGO_ANCHO= env('LOGO_ANCHO')
LOGO_ALTO= env('LOGO_ALTO')
BARRA= env('BARRA')
BARRA_ALTO= env('BARRA_ALTO')
DESCRIPCION= env('DESCRIPCION')
REGISTRO = env('REGISTRO')

UNFOLD = {
    # Otros ajustes...
    "SITE_LOGO": {
        "light": lambda request: static(LOGO),
        "dark": lambda request: static(LOGO),
    },
    "SITE_TITLE": NOMBRE,
    "SITE_HEADER": NOMBRE,
    # Otros ajustes...
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0','200.12.134.76',]

# Formato de entrada de fecha para formularios
DATE_INPUT_FORMATS = ['%d/%m/%Y']

# Formato de visualización de fecha (por ejemplo, en plantillas)
DATE_FORMAT = 'd/m/Y'


# Application definition
#FORCE_SCRIPT_NAME = '/turismo'

INSTALLED_APPS = [
    #'jazzmin',
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",  # optional, if special filters are needed
    "unfold.contrib.forms",  # optional, if special form elements are needed
    "unfold.contrib.inlines",  # optional, if special inlines are needed
    "unfold.contrib.simple_history",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
 
    # 3rd party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'materializecssform',
    #'hitcount',
    'corsheaders',
    'imagekit',
    'widget_tweaks',
    'simple_history',

    # local
    'accounts',
    'captcha',
    'comedor',
    'persona',
    'salud',


    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    #django corse headers
    "corsheaders.middleware.CorsMiddleware",
    #
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'src.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'src.context_processors.variable_global',
            ],
        },
    },
]

WSGI_APPLICATION = 'src.wsgi.application'

#DISABLE_SERVER_SIDE_CURSORS = True
# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

'''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}'''

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

else:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env('POSTGRESQL_NAME'),
            'USER': env('POSTGRESQL_USER'),
            'PASSWORD': env('POSTGRESQL_PASS'),
            'HOST': env('POSTGRESQL_HOST'),
            'PORT': env('POSTGRESQL_PORT'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "es"

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATIC_URL = '/static/'
#STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'

#ACCOUNT_SIGNUP_FORM_CLASS = 'accounts.forms.CustomUserCreationForm'

# for allauth
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True
#EMAIL_HOST_USER = 'a.test@a.uncu.edu.ar'  # Reemplaza con tu correo
#EMAIL_HOST_PASSWORD = 'a'    # Reemplaza con tu contraseña o contraseña de aplicación

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

ACCOUNT_SIGNUP_REDIRECT_URL = '/accounts/seleccionar-rol/'
# Formulario personalizado para signup
ACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSignupForm',
}


CORS_ALLOWED_ORIGINS = [
        'http://127.0.0.1:8000'
    ]

CORS_ALLOW_ALL_ORIGINS = True

HITCOUNT_KEEP_HIT_IN_DATABASE = { 'days': 30 }
HITCOUNT_KEEP_HIT_ACTIVE = { 'days': 1 }

"""
Django settings for webscanner project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.utils.translation import gettext_lazy as _

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
VAR_DIR = os.path.join(PROJECT_DIR, 'var')
LOGS_DIR = os.path.join(VAR_DIR, 'logs')

MEDIA_ROOT = os.path.join(PROJECT_DIR, 'webscanner_site/uploads')

DEBUG = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS':
            [
                'BASE_DIR/django-os2webscanner/os2webscanner/templates'
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
]

SITE_ID = 1

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'os2webscanner.apps.OS2WebScanner',
    'recurrence',
    'django_xmlrpc',
)

XMLRPC_METHODS = (
    ('os2webscanner.rpc.scan_urls', 'scan_urls'),
    ('os2webscanner.rpc.scan_documents', 'scan_documents'),
    ('os2webscanner.rpc.get_status', 'get_status'),
    ('os2webscanner.rpc.get_report', 'get_report'),
)
MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'webscanner.urls'

WSGI_APPLICATION = 'webscanner.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'da-dk'

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, 'django-os2webscanner/os2webscanner/locale/'),
)

LANGUAGES = (
    ('da', _('Danish')),
    ('en', _('English')),
)

TIME_ZONE = 'Europe/Copenhagen'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + '/static'
AUTH_PROFILE_MODULE = 'os2webscanner.UserProfile'

LOGIN_REDIRECT_URL = '/'

# Email settings

DEFAULT_FROM_EMAIL = 'os2webscanner@magenta.dk'
ADMIN_EMAIL = 'os2webscanner@magenta.dk'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Enable groups - or not

DO_USE_GROUPS = False

# Use MD5 sums.
# This should practically always be true, but we might want to disable it for
# debugging uses. At some point, this could also become a parameter on the
# scanner.

DO_USE_MD5 = False

# The threshold for number of OCR conversion queue items per scan above which
# non-OCR conversion will be paused. The reason to have this feature is that
# for large scans with OCR enabled, so many OCR items are extracted from
# PDFs or Office documents that it exhausts the number of available inodes
# on the filesystem. Pausing non-OCR conversions allows the OCR processors a
# chance to process their queue items to below a reasonable level.
PAUSE_NON_OCR_ITEMS_THRESHOLD = 2000

# The threshold for number of OCR conversion queue items per scan below which
# non-OCR conversion will be resumed. This must be a lower number than
# PAUSE_NON_OCR_ITEMS_THRESHOLD.
RESUME_NON_OCR_ITEMS_THRESHOLD = PAUSE_NON_OCR_ITEMS_THRESHOLD - 1000

# Directory to store files transmitted by RPC
RPC_TMP_PREFIX = '/tmp/os2webscanner'

# Directory to mount network drives
NETWORKDRIVE_TMP_PREFIX = '/tmp/mnt/os2webscanner/'

# Always store temp files on disk
FILE_UPLOAD_MAX_MEMORY_SIZE = 0

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': VAR_DIR + '/debug.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'os2webscanner': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

local_settings_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'local_settings.py'
)
if os.path.exists(local_settings_file):
    from .local_settings import *
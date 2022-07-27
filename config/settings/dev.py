from config.settings.base import *  # noqa: F403


DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

SECRET_KEY = env('SECRET_KEY', default='test_key')

ALLOWED_HOSTS = ['*']
INTERNAL_IPS = ['127.0.0.1']

ADMINS = (
    ('Dev Email', env('DEV_ADMIN_EMAIL', default='admin@localhost')),
)
MANAGERS = ADMINS


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
# --------------------------------------------------------------------------

DATABASES = {
    'default': env.db(default='postgres://localhost/aqua_voting_tracker'),
}


# Email settings
# --------------------------------------------------------------------------

DEFAULT_FROM_EMAIL = 'noreply@example.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if CELERY_ENABLED:
    MAILING_USE_CELERY = False


# Debug toolbar installation
# --------------------------------------------------------------------------

INSTALLED_APPS += (
    'debug_toolbar',
)

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
INTERNAL_IPS = ('127.0.0.1',)


if CELERY_ENABLED:
    # Celery configurations
    # http://docs.celeryproject.org/en/latest/configuration.html
    # --------------------------------------------------------------------------

    CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='amqp://guest@localhost//')

    CELERY_TASK_ALWAYS_EAGER = True


# Sentry config
# -------------

SENTRY_ENABLED = False


# Horizon configuration
# --------------------------------------------------------------------------

STELLAR_PASSPHRASE = 'Test SDF Network ; September 2015'
HORIZON_URL = 'https://horizon-testnet.stellar.org'


# Voting configuration
# --------------------------------------------------------------------------

VOTING_ASSET_CODE = 'TEST'
VOTING_ASSET_ISSUER = 'GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO'

VOTING_ASSETS = [
    'TEST:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO',
    'TEST2:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO',
    # Secret key: SBUQ5JLWL47QI74KI6I2GMESVV644R4V5VA3VC6T3Q3YKHTODYVJP23O
]
VOTING_BALANCES_DISTRIBUTOR = 'GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO'

MARKETKEYS_TRACKER_URL = 'http://localhost:8001'

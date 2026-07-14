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


# Cache
# --------------------------------------------------------------------------
# Shared cache is required: voting-rewards are computed by a celery/shell
# process and read by the API process. The default LocMemCache is
# per-process, so the API would never see the computed rewards.

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('CACHE_URL', default='redis://127.0.0.1:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'aquavotingtracker',
    },
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

# Testnet ICE distributor assets (issued for locking testnet AQUA).
TESTNET_ICE_ISSUER = 'GAYYH44SS4OSFDY4WXMWM2BKRA2RG5M6NZULUQWGHKGFASFY2ZVI7IHX'

VOTING_ASSETS = env.list('VOTING_ASSETS', default=[
    f'upvoteICE:{TESTNET_ICE_ISSUER}',
    f'dICE:{TESTNET_ICE_ISSUER}',
])
VOTING_BALANCES_DISTRIBUTOR = env('VOTING_BALANCES_DISTRIBUTOR', default=TESTNET_ICE_ISSUER)

MARKETKEYS_TRACKER_URL = env('MARKETKEYS_TRACKER_URL', default='http://localhost:8000')


# Voting reward configuration
# --------------------------------------------------------------------------

SOROBAN_SHARE_BOOST = Decimal(env('SOROBAN_SHARE_BOOST', default='1'))

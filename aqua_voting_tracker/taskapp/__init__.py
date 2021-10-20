import os

from django.conf import settings

from celery import Celery
from celery.schedules import crontab

if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('aqua_voting_tracker')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.timezone = 'UTC'


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    app.conf.beat_schedule.update({
        'aquarius.voting.tasks.task_load_new_claimable_balances': {
            'task': 'aquarius.voting.tasks.task_load_new_claimable_balances',
            'schedule': crontab(minute='*/5'),
            'args': (),
        },
        'aquarius.voting.tasks.task_create_voting_snapshot': {
            'task': 'aquarius.voting.tasks.task_create_voting_snapshot',
            'schedule': crontab(hour=0, minute=10),
            'args': (),
        },
    })

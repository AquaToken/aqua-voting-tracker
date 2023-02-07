import logging

from django.core.management import BaseCommand

from prometheus_client import start_http_server

from aqua_voting_tracker.voting.loaders.effects import EffectsStream


class Command(BaseCommand):
    help = 'Start a SSE client to listen horizon effects.'

    def add_arguments(self, parser):
        parser.add_argument('--metrics-port', nargs='?', default=9954,
                            help='Port to use by prometheus exporter.')

    def set_up_logger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(self.stdout)
        logger.addHandler(handler)

    def handle(self, *args, **options):
        self.set_up_logger()

        start_http_server(options['metrics_port'])

        EffectsStream().run()

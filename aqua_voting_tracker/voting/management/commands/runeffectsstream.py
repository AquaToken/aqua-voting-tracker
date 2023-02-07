import logging

from django.core.management import BaseCommand

from aqua_voting_tracker.voting.loaders.effects import EffectsStream


class Command(BaseCommand):
    def set_up_logger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(self.stdout)
        logger.addHandler(handler)

    def handle(self, *args, **options):
        self.set_up_logger()

        EffectsStream().run()

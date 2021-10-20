from django.conf import settings

from stellar_sdk import Asset


def get_voting_asset():
    return Asset(settings.VOTING_ASSET_CODE, settings.VOTING_ASSET_ISSUER)

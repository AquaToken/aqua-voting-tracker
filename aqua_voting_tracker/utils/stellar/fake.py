import random
import string

from faker.providers import BaseProvider
from stellar_sdk import Asset, Keypair

from aqua_voting_tracker.utils.stellar.asset import get_asset_string


class StellarProvider(BaseProvider):
    def stellar_keypair(self):
        return Keypair.random()

    def stellar_public_key(self):
        return self.stellar_keypair().public_key

    def stellar_asset(self):
        code = ''.join(random.choice(string.ascii_uppercase) for i in range(4))
        return Asset(code, self.stellar_public_key())

    def stellar_asset_string(self):
        return get_asset_string(self.stellar_asset())

    def stellar_claimable_balance_id(self):
        abc = string.digits + 'abcdef'
        return '00000000' + ''.join(random.choice(abc) for i in range(64))

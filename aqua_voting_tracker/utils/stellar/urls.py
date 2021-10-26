from stellar_sdk import Asset
from stellar_sdk.exceptions import AssetIssuerInvalidError

from aqua_voting_tracker.utils.stellar.asset import get_asset_string, parse_asset_string


class AssetStringConverter:
    code_regex = '[a-zA-Z0-9]{1,12}'
    issuer_regex = 'G[a-zA-Z0-9]{55}'
    regex = f'(native)|({code_regex}:{issuer_regex})'

    def to_python(self, value: str) -> Asset:
        try:
            return parse_asset_string(value)
        except AssetIssuerInvalidError as e:
            raise ValueError('Invalid asset.') from e

    def to_url(self, asset: Asset) -> str:
        return get_asset_string(asset)

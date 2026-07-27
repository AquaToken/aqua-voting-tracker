from stellar_sdk import Asset


def get_asset_string(asset: Asset) -> str:
    if asset.is_native():
        return 'native'

    return f'{asset.code}:{asset.issuer}'


def parse_asset_string(asset_string: str) -> Asset:
    if asset_string == 'native':
        return Asset.native()

    code, issuer = asset_string.split(':')
    return Asset(code, issuer)


def is_contract_asset_string(asset_string: str) -> bool:
    """Soroban assets are serialized as a bare contract id (C...), classic ones as CODE:ISSUER or 'native'."""
    return asset_string.startswith('C') and ':' not in asset_string and len(asset_string) == 56

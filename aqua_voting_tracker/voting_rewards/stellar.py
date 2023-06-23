import asyncio
import math
from typing import Iterable, List, Optional, Tuple

from stellar_sdk import Asset, ServerAsync

from aqua_voting_tracker.utils.stellar.asset import get_asset_string


class AMM:
    def __init__(self, reserve1: float, reserve2: float, fee: float):
        self.reserve1 = reserve1
        self.reserve2 = reserve2
        self.fee = fee

    def reverse(self):
        return self.__class__(self.reserve2, self.reserve1, self.fee)

    def depth(self, price: float) -> float:
        return self.reserve2 - self.reserve1 / (price * (1 - self.fee))

    @property
    def min_price(self) -> float:
        return self.reserve1 / (self.reserve2 * (1 - self.fee))

    @classmethod
    async def load_from_horizon(cls, asset1: Asset, asset2: Asset, server: ServerAsync) -> Optional['AMM']:
        response = await server.liquidity_pools().for_reserves([asset1, asset2]).call()
        records = response['_embedded']['records']

        if not records:
            return None

        liquidity_pool = records[0]
        asset_string1 = get_asset_string(asset1)
        asset_string2 = get_asset_string(asset2)
        reserve1 = next(filter(lambda r: r['asset'] == asset_string1, liquidity_pool['reserves']))
        reserve2 = next(filter(lambda r: r['asset'] == asset_string2, liquidity_pool['reserves']))

        return cls(
            float(reserve1['amount']),
            float(reserve2['amount']),
            float(liquidity_pool['fee_bp']) / 10000,
        )


class SDEX:
    def __init__(self, prices: List[float], depth: List[float]):
        self.prices = prices
        self.depth = depth

    @property
    def min_price(self) -> float:
        return self.prices[0]

    def get_depth_segments(self) -> Iterable[Tuple[float, float, float]]:
        prev_price = self.prices[0]
        for price, depth in zip(self.prices[1:], self.depth[:-1]):
            yield depth, prev_price, price

            prev_price = price

        yield self.depth[-1], self.prices[-1], math.inf

    @classmethod
    async def load_from_horizon(cls, buy_asset: Asset, sell_asset: Asset, server: ServerAsync) -> Optional['SDEX']:
        prices_amount_dict = {}
        cursor = None
        while True:
            request = server.offers().for_buying(buy_asset).for_selling(sell_asset).limit(200).order(desc=True)
            if cursor:
                request = request.cursor(cursor)
            records = (await request.call())['_embedded']['records']

            for offer in records:
                price = (offer['price_r']['n'], offer['price_r']['d'])
                if price not in prices_amount_dict:
                    prices_amount_dict[price] = 0

                prices_amount_dict[price] += float(offer['amount'])

                cursor = offer['paging_token']

            if len(records) < 200:
                break

        if not prices_amount_dict:
            return None

        aggregated_offers = sorted(
            [(float(n) / float(d), amount) for (n, d), amount in prices_amount_dict.items()])

        accumulator = 0
        prices = []
        depth = []
        for price, amount in aggregated_offers:
            accumulator += amount
            prices.append(price)
            depth.append(accumulator)

        return cls(prices, depth)


class MarketData:
    amm = None
    buying_sdex = None
    selling_sdex = None

    def __init__(self, asset1: Asset, asset2: Asset):
        self.asset1 = asset1
        self.asset2 = asset2

    @property
    def buying_min_price(self) -> float:
        sdex = self.buying_sdex
        amm = self.amm
        return min(sdex.min_price, amm.min_price)

    @property
    def selling_min_price(self) -> float:
        sdex = self.selling_sdex
        amm = self.amm.reverse()
        return min(sdex.min_price, amm.min_price)

    async def load_amm(self, server: ServerAsync):
        self.amm = await AMM.load_from_horizon(self.asset1, self.asset2, server)

    async def load_sdex_buying(self, server: ServerAsync):
        self.buying_sdex = await SDEX.load_from_horizon(self.asset1, self.asset2, server)

    async def load_sdex_selling(self, server: ServerAsync):
        self.selling_sdex = await SDEX.load_from_horizon(self.asset2, self.asset1, server)

    async def load_data(self, server: ServerAsync):
        await asyncio.gather(
            self.load_amm(server),
            self.load_sdex_buying(server),
            self.load_sdex_selling(server),
        )

    def is_loaded(self) -> bool:
        return all(component is not None for component in [self.amm, self.buying_sdex, self.selling_sdex])

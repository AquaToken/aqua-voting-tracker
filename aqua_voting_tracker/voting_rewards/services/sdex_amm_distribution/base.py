import logging

from aqua_voting_tracker.voting_rewards.stellar import MarketData


logger = logging.getLogger(__name__)


class Distributor:
    def __init__(self, market_data: MarketData):
        self.market_data = market_data

    def get_sdex_buying_weight(self) -> float:
        raise NotImplementedError

    def get_sdex_selling_weight(self) -> float:
        raise NotImplementedError

    def get_amm_buying_weight(self) -> float:
        raise NotImplementedError

    def get_amm_selling_weight(self) -> float:
        raise NotImplementedError

    def get_weights(self) -> (float, float):
        sdex_buying_weight = self.get_sdex_buying_weight()
        sdex_selling_weight = self.get_sdex_selling_weight()
        amm_buying_weight = self.get_amm_buying_weight()
        amm_selling_weight = self.get_amm_selling_weight()

        logger.debug('SDEX buy weight: %s', sdex_buying_weight)
        logger.debug('AMM buy weight: %s', amm_buying_weight)
        logger.debug('SDEX sell weight: %s', sdex_selling_weight)
        logger.debug('AMM sell weight: %s', amm_selling_weight)

        buying_sum = sdex_buying_weight + amm_buying_weight
        selling_sum = sdex_selling_weight + amm_selling_weight

        sdex_buying_weight = sdex_buying_weight / buying_sum
        sdex_selling_weight = sdex_selling_weight / selling_sum
        amm_buying_weight = amm_buying_weight / buying_sum
        amm_selling_weight = amm_selling_weight / selling_sum

        sdex_weight = (sdex_buying_weight + sdex_selling_weight) / 2
        amm_weight = (amm_buying_weight + amm_selling_weight) / 2

        logger.debug('SDEX weight: %s', sdex_weight)
        logger.debug('AMM weight: %s', amm_weight)

        return sdex_weight, amm_weight

import logging
import math

from aqua_voting_tracker.voting_rewards.integrate import integrate, integrate_piecewise
from aqua_voting_tracker.voting_rewards.services.sdex_amm_distribution.base import Distributor


logger = logging.getLogger(__name__)


class ExponentDistributor(Distributor):
    def exponent(self, price: float, min_price: float) -> float:
        return (min_price / price) ** 8

    def get_sdex_buying_weight(self) -> float:
        sdex = self.market_data.buying_sdex
        min_price = self.market_data.buying_min_price

        result, error = integrate_piecewise(self.exponent, sdex.get_depth_segments(), args=(min_price, ))
        logger.debug('SDEX buying error: %s', error)
        return result

    def get_sdex_selling_weight(self) -> float:
        sdex = self.market_data.selling_sdex
        min_price = self.market_data.selling_min_price

        result, error = integrate_piecewise(self.exponent, sdex.get_depth_segments(), args=(min_price, ))
        logger.debug('SDEX selling error: %s', error)
        return result

    def get_amm_buying_weight(self) -> float:
        amm = self.market_data.amm
        min_price = self.market_data.buying_min_price

        result, error = integrate(lambda price: self.exponent(price, min_price) * amm.depth(price),
                                  amm.min_price, math.inf)
        logger.debug('AMM buying error: %s', error)
        return result

    def get_amm_selling_weight(self) -> float:
        amm = self.market_data.amm.reverse()
        min_price = self.market_data.selling_min_price

        result, error = integrate(lambda price: self.exponent(price, min_price) * amm.depth(price),
                                  amm.min_price, math.inf)
        logger.debug('AMM selling error: %s', error)
        return result

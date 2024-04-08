from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
from copy import deepcopy

empty_dict = {'AMETHYSTS': 0, 'STARFRUIT': 0}


class Trader:
    def ordersSimpleMarketMaking(self, product: str):
        pass


    def run(self, state: TradingState):
    positions = deepcopy(empty_dict)

        for product in state.position:
            positions[product] = state.position[product]
            


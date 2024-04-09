from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict

class Trader:

    def ordersSimpleMarketMaking(self, product: str, order_depth: OrderDepth, position: int, positionLimit: int, fair_price: int) -> List[Order]:
    
        best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

        best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]

        maxToBuy = positionLimit - position # positive number -> max is 40 
        maxToSell = position + positionLimit # positive number -> max is 40

        print("product: " + product)
        print("order book: (buy then sell)" + str(order_depth.buy_orders) + " " + str(order_depth.sell_orders))
        print("best bid: " + str(best_bid) + " best ask: " + str(best_ask))
        print("position: " + str(position) + " position limit: " + str(positionLimit))
        print("max to buy: " + str(maxToBuy) + " max to sell: " + str(maxToSell))

        orders: List[Order] = []

        for ask, amount in reversed(order_depth.sell_orders.items()):
            if ask < fair_price:
                #amount is a negative number
                #submit a positive number to buy
                if -amount > maxToBuy:
                    orders.append(Order(product, ask, maxToBuy))
                    maxToBuy = 0
                else:
                    orders.append(Order(product, ask, -amount))
                    maxToBuy += amount


        for bid, amount in reversed(order_depth.buy_orders.items()):
            if bid > fair_price:
                #amount is a positive number
                #submit a negative number to sell
                if amount > maxToSell:
                    orders.append(Order(product, bid, -maxToSell))
                    maxToSell = 0
                else:
                    orders.append(Order(product, bid, -amount))
                    maxToSell += amount
                
        if(maxToBuy > 0):
            orders.append(Order(product, best_bid + 2, maxToBuy))

        if(maxToSell < 0):
            orders.append(Order(product, best_ask - 2, -maxToSell))

        print("orders: " + str(orders))

        return orders


    def run(self, state: TradingState):
        position_limits = {'AMETHYSTS': 20, 'STARFRUIT': 20}
        result = {}
        result['AMETHYSTS'] = self.ordersSimpleMarketMaking('AMETHYSTS', state.order_depths['AMETHYSTS'], state.position.get('AMETHYSTS', 0), position_limits['AMETHYSTS'], 10000)
        result['STARFRUIT'] = self.ordersSimpleMarketMaking('STARFRUIT', state.order_depths['STARFRUIT'], state.position.get('STARFRUIT', 0), position_limits['STARFRUIT'], 5000)
        return result, 0, "hi"
            


from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import math
import jsonpickle
import numpy as np

class Trader:
    def ordersSimpleMarketMaking(self, product: str, order_depth: OrderDepth, position: int, positionLimit: int, fair_price: int, bid_ask_spread) -> List[Order]:

        best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
        best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

        maxToBuy = positionLimit - position # positive number -> max is 40 
        maxToSell = position + positionLimit # positive number -> max is 40

        orders: List[Order] = []

        #market taking. Doesn't generate very much profit but occasionally makes money

        # reverse order shows the best deals first
        for ask, amount in reversed(order_depth.sell_orders.items()):
            if ask < fair_price:
                #amount is a negative number
                #submit a positive number to buy
                if (-amount) > maxToBuy:
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
                    maxToSell -= amount
        
        #market making. Generates more profit
        
        # Calculate final buy and sell prices enforcing the bid-ask spread
        final_buy_price = int(math.floor(fair_price - bid_ask_spread))
        final_sell_price = int(math.ceil(fair_price + bid_ask_spread))

        if(maxToBuy > 0):
            orders.append(Order(product, final_buy_price, maxToBuy))

        if(maxToSell > 0):
            orders.append(Order(product, final_sell_price, -maxToSell))
            
        #print("simple orders: " + str(orders))

        return orders

    def run(self, state: TradingState):
        POSITION_LIMITS = {'AMETHYSTS': 20, 'STARFRUIT': 20}
        BID_ASK_SPREADS = {'AMETHYSTS': 3, 'STARFRUIT': 2} #half of spread
        pInformed = {'AMETHYSTS': 0, 'STARFRUIT': 0.4}
        STARFRUIT_DATA_LENGTH = 5
        result = {}
        #######################
        #Amethysts
        #######################
        result['AMETHYSTS'] = self.ordersSimpleMarketMaking('AMETHYSTS', state.order_depths['AMETHYSTS'], state.position.get('AMETHYSTS', 0), POSITION_LIMITS['AMETHYSTS'], 10000, BID_ASK_SPREADS['AMETHYSTS'])

        #######################
        #Starfruit
        #######################

        decoded_data = {}
        if state.traderData:
            try:
                decoded_data = jsonpickle.decode(state.traderData)
            except Exception as e:
                print(f"Error decoding traderData: {e}")
                # Handle the exception appropriately, maybe log it or set a default value
                # For this example, decoded_data remains an empty dictionary

        # Check if 'STARFRUIT_HISTORY' exists in decoded_data, otherwise initialize it
        starfruit_fair_price = decoded_data.get('STARFRUIT_FAIR_PRICE', 0)
        if starfruit_fair_price == 0:
            print("Lost fair price data")
            starfruit_price = 0
            starfruit_volume = 0
            for ask, amount in state.order_depths['STARFRUIT'].sell_orders.items():
                starfruit_price += abs(ask*amount)
                starfruit_volume += abs(amount)

            for bid, amount in state.order_depths['STARFRUIT'].buy_orders.items():
                starfruit_price += abs(bid*amount)
                starfruit_volume += abs(amount)

            if starfruit_volume != 0:
                starfruit_fair_price = starfruit_price / starfruit_volume
            else:
                starfruit_fair_price = 5000 #lets hope it doesn't get here
                print("No volume")

        print(state.own_trades.get('STARFRUIT', []))

        old_price = starfruit_fair_price

        if len(state.own_trades.get('STARFRUIT', [])) > 0:
            for trade in state.own_trades['STARFRUIT']:
                if trade.timestamp == state.timestamp - 100:
                    starfruit_fair_price = starfruit_fair_price + (trade.price - old_price) * pInformed['STARFRUIT']
                    print("old price: " + str(old_price) + " new price: " + str(starfruit_fair_price))

        result['STARFRUIT'] = self.ordersSimpleMarketMaking('STARFRUIT', state.order_depths['STARFRUIT'], state.position.get('STARFRUIT', 0), POSITION_LIMITS['STARFRUIT'], starfruit_fair_price, BID_ASK_SPREADS['STARFRUIT'])

        #######################
        #Output and Other
        #######################
        
        traderData = {'STARFRUIT_FAIR_PRICE': starfruit_fair_price}

        return result, 0, jsonpickle.encode(traderData)
            


from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import math
import jsonpickle

class Trader:

    def ordersSimpleMarketMaking(self, product: str, order_depth: OrderDepth, position: int, positionLimit: int, fair_price: int, PRICE_ADJUSTMENTS: Dict[int, int], bid_ask_spread) -> List[Order]:
    
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

        #market taking. Doesn't generate very much profit 

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

        midpoint_adjustment = 0
        for threshold, adj in PRICE_ADJUSTMENTS:
            if position >= threshold:
                print("position: " + str(position) + " threshold: " + str(threshold) + " adj: " + str(adj))
                midpoint_adjustment = adj
                break
        
        # Adjust the midpoint based on the position
        adjusted_midpoint = fair_price + midpoint_adjustment
        
        # Calculate final buy and sell prices enforcing the bid-ask spread
        final_buy_price = int(math.floor(adjusted_midpoint - bid_ask_spread))
        final_sell_price = int(math.ceil(adjusted_midpoint + bid_ask_spread))

        if(maxToBuy > 0):
            orders.append(Order(product, final_buy_price, maxToBuy))

        if(maxToSell > 0):
            orders.append(Order(product, final_sell_price, -maxToSell))

        print("orders: " + str(orders))

        return orders

    def run(self, state: TradingState):
        POSITION_LIMITS = {'AMETHYSTS': 20, 'STARFRUIT': 20}
        #PRICE_ADJUSTMENTS = {'AMETHYSTS': [(15, 1), (-15,0), (-20, -1)], 'STARFRUIT': [(10, 1), (0, 0), (-10, 1)]}
        PRICE_ADJUSTMENTS = {'AMETHYSTS': [(-20, 0)], 'STARFRUIT': [(-20, 0)]} #price adjustments is just not working
        BID_ASK_SPREADS = {'AMETHYSTS': 3, 'STARFRUIT': 2} #half of spread
        result = {}
        result['AMETHYSTS'] = self.ordersSimpleMarketMaking('AMETHYSTS', state.order_depths['AMETHYSTS'], state.position.get('AMETHYSTS', 0), POSITION_LIMITS['AMETHYSTS'], 10000, PRICE_ADJUSTMENTS['AMETHYSTS'], BID_ASK_SPREADS['AMETHYSTS'])

        STARFRUIT_DATA_LENGTH = 5   

        decoded_data = {}
        if state.traderData:
            try:
                decoded_data = jsonpickle.decode(state.traderData)
            except Exception as e:
                print(f"Error decoding traderData: {e}")
                # Handle the exception appropriately, maybe log it or set a default value
                # For this example, decoded_data remains an empty dictionary

# Check if 'STARFRUIT_HISTORY' exists in decoded_data, otherwise initialize it
        starfruit_history = decoded_data.get('STARFRUIT_HISTORY', [])
        starfruit_best_ask = list(state.order_depths['STARFRUIT'].sell_orders.items())[0]
        starfruit_best_bid = list(state.order_depths['STARFRUIT'].buy_orders.items())[0]
        starfruit_midpoint = (starfruit_best_ask[0] + starfruit_best_bid[0]) / 2
        starfruit_history.append(starfruit_midpoint)
        starfruit_history = starfruit_history[-STARFRUIT_DATA_LENGTH:]
        starfruit_fair_price = sum(starfruit_history) / len(starfruit_history)

        result['STARFRUIT'] = self.ordersSimpleMarketMaking('STARFRUIT', state.order_depths['STARFRUIT'], state.position.get('STARFRUIT', 0), POSITION_LIMITS['STARFRUIT'], starfruit_fair_price, PRICE_ADJUSTMENTS['STARFRUIT'], BID_ASK_SPREADS['STARFRUIT'])

        traderData = {'STARFRUIT_HISTORY': starfruit_history}
        
        return result, 0, jsonpickle.encode(traderData)
            


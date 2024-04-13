from datamodel import OrderDepth, UserId, TradingState, Order, ConversionObservation, Observation
from typing import List, Dict, Tuple
import math
import jsonpickle
import numpy as np

class Trader:
    def predict_next(self, sequence: list[float]) -> float:
        coef = [-0.15, -0.05,  0.05,  0.15,  1] #gets 3.21K
        #coef = [1]
        if(len(sequence) != len(coef)):
            #print("Invalid sequence length, returning last value")
            return sequence[-1]
        
        next_price = 0
        for i, val in enumerate(sequence):
            next_price += val * coef[i]

        return next_price

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
    
    def orchidArbitrage(self, order_depth: OrderDepth, position: int, positionLimit: int, orchid_state: str, obs: ConversionObservation, ownTrades: List[Order], timestamp: int) -> Tuple[List[Order], int, str]:
        north_best_bid, north_best_bid_amount = list(order_depth.buy_orders.items())[0]
        north_best_ask, north_best_ask_amount = list(order_depth.sell_orders.items())[0]

        #adjusted is how much we pay or we would get paid
        north_adjusted_best_ask = north_best_ask - 0.1*north_best_ask_amount

        south_bid = obs.bidPrice
        south_ask = obs.askPrice

        south_adjusted_bid = south_bid - obs.exportTariff - obs.transportFees
        south_adjusted_ask = south_ask + obs.importTariff + obs.transportFees

        maxToBuy = positionLimit - position # positive number -> max is 40 
        maxToSell = position + positionLimit # positive number -> max is 40

        print("Current State: ", orchid_state)
        print("Position: ", position)
        print("North Market - Best Bid: ", north_best_bid,)
        print("North Market - Best Ask: ", north_best_ask, " Adjusted Ask: ", north_adjusted_best_ask)
        print("Import Tariff: ", obs.importTariff, " Export Tariff: ", obs.exportTariff, " Transport Fees: ", obs.transportFees)
        print("South Market - Bid: ", south_bid, " Adjusted Bid: ", south_adjusted_bid)
        print("South Market - Ask: ", south_ask, " Adjusted Ask: ", south_adjusted_ask)

        conversion_requests = 0

        if orchid_state == "convert next":
            print("Action: Convert next - clearing position")
            conversion_requests = abs(position)

        if orchid_state == "watch for conversion":
            if len(ownTrades) > 0:
                for trade in ownTrades:
                    if trade.timestamp == timestamp - 100:
                        print("Action: Performing conversion - clearing position")
                        conversion_requests = abs(position)
                print("No trade found - no conversion performed")

        if north_best_bid > south_adjusted_ask:
            print("Action: Buying on South, Selling on North - Immediate arbitrage opportunity")
            return [Order("ORCHIDS", north_best_bid, -north_best_bid_amount)], conversion_requests, "convert next"

        if north_adjusted_best_ask < south_adjusted_bid:
            print("Action: Buying at North Ask, Selling at South Bid - Immediate arbitrage opportunity")
            return [Order("ORCHIDS", north_best_ask, -north_best_ask_amount)], conversion_requests, "convert next"

        if north_best_bid > south_adjusted_bid and north_adjusted_best_ask > south_adjusted_ask:
            print("Action: Submit limit order on North (higher ask), immediate convert if filled")
            return [Order("ORCHIDS", north_best_ask, -maxToSell)], conversion_requests, "watch for conversion"

        if north_best_bid < south_adjusted_bid and north_adjusted_best_ask < south_adjusted_ask:
            print("Action: Submit limit order on North (lower bid), immediate convert if filled")
            return [Order("ORCHIDS", north_best_bid, maxToBuy)], conversion_requests, "watch for conversion"

        print("No viable action found - maintaining current state")
        return [], conversion_requests, "none"


    def run(self, state: TradingState):
        POSITION_LIMITS = {'AMETHYSTS': 20, 'STARFRUIT': 20, 'ORCHIDS': 100}
        BID_ASK_SPREADS = {'AMETHYSTS': 3, 'STARFRUIT': 1.9} #half of spread
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
        starfruit_history = decoded_data.get('STARFRUIT_HISTORY', [])
        starfruit_price = 0
        starfruit_volume = 0
        for ask, amount in state.order_depths['STARFRUIT'].sell_orders.items():
            starfruit_price += abs(ask*amount)
            starfruit_volume += abs(amount)

        for bid, amount in state.order_depths['STARFRUIT'].buy_orders.items():
            starfruit_price += abs(bid*amount)
            starfruit_volume += abs(amount)

        if starfruit_volume != 0:
            starfruit_midpoint = starfruit_price / starfruit_volume
        else:
            starfruit_midpoint = starfruit_history[-1]

        starfruit_history.append(starfruit_midpoint)
        starfruit_history = starfruit_history[-STARFRUIT_DATA_LENGTH:]
        starfruit_fair_price = self.predict_next(starfruit_history)

        result['STARFRUIT'] = self.ordersSimpleMarketMaking('STARFRUIT', state.order_depths['STARFRUIT'], state.position.get('STARFRUIT', 0), POSITION_LIMITS['STARFRUIT'], starfruit_fair_price, BID_ASK_SPREADS['STARFRUIT'])

        # if 'AMETHYSTS' in state.market_trades or 'STARFRUIT' in state.market_trades:
        #     print("Trades we missed out on: ")

        #     if 'AMETHYSTS' in state.market_trades:
        #         for trade in state.market_trades['AMETHYSTS']:
        #             if trade.buyer != "SUBMISSION" and trade.seller != "SUBMISSION":
        #                 print(" " + str(trade))

        #     if 'STARFRUIT' in state.market_trades:
        #         print("Starfruit fair price: " + str(starfruit_fair_price) + " ")
        #         for trade in state.market_trades['STARFRUIT']:
        #             if trade.buyer != "SUBMISSION" and trade.seller != "SUBMISSION":
        #                 print(str(trade) + " " + str(abs(trade.price - starfruit_fair_price)) + " ")

        # else:
        #     print("No trades missed")

        #######################
        #Orchids
        #######################

        orchid_data = decoded_data.get('ORCHID_DATA', "none")
        result['ORCHIDS'], conversion_requests, orchid_data = self.orchidArbitrage(state.order_depths['ORCHIDS'], state.position.get('ORCHIDS', 0), POSITION_LIMITS['ORCHIDS'], orchid_data, state.observations.conversionObservations['ORCHIDS'], state.own_trades.get('ORCHIDS', []), state.timestamp)
        traderData = {'STARFRUIT_HISTORY': starfruit_history, 'ORCHID_DATA': orchid_data}
        return result, conversion_requests, jsonpickle.encode(traderData)
            


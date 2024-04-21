from datamodel import OrderDepth, UserId, TradingState, Order, ConversionObservation, Observation
from typing import List, Dict, Tuple
import math
import jsonpickle
import numpy as np

class Trader:
    def predict_next(self, sequence: list[float]) -> float:
        #coef = [-0.15, -0.05,  0.05,  0.15,  1] #gets 3.21K
        coef = [1]
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
    
    def orchidArbitrage(self, order_depth: OrderDepth, position: int, positionLimit: int, obs: ConversionObservation, ownTrades: List[Order], timestamp: int) -> Tuple[List[Order], int]:
        north_best_bid, north_best_bid_amount = list(order_depth.buy_orders.items())[0]
        north_best_ask, north_best_ask_amount = list(order_depth.sell_orders.items())[0]

        #adjusted is how much we pay or we would get paid
        north_adjusted_best_ask = north_best_ask - 0.1*north_best_ask_amount

        south_bid = obs.bidPrice
        south_ask = obs.askPrice

        south_adjusted_bid = south_bid - obs.exportTariff - obs.transportFees
        south_adjusted_ask = south_ask + obs.importTariff + obs.transportFees

        maxToBuy = 100 # positive number -> max is 40 
        maxToSell = 100 # positive number -> max is 40

        # print("Position: ", position)
        # print("North Market - Best Bid: ", north_best_bid,)
        # print("North Market - Best Ask: ", north_best_ask, " Adjusted Ask: ", north_adjusted_best_ask)
        # print("Import Tariff: ", obs.importTariff, " Export Tariff: ", obs.exportTariff, " Transport Fees: ", obs.transportFees)
        # print("South Market - Bid: ", south_bid, " Adjusted Bid: ", south_adjusted_bid)
        # print("South Market - Ask: ", south_ask, " Adjusted Ask: ", south_adjusted_ask)

        conversion_requests = abs(position)
        orders = []
        total_bids = 0

        # very extreme arbitrage
        for bid, amount in reversed(order_depth.buy_orders.items()):
            total_bids += amount
            if bid > south_adjusted_ask:
                if amount > maxToSell:
                    orders.append(Order("ORCHIDS", bid, -maxToSell))
                    maxToSell = 0
                else:
                    orders.append(Order("ORCHIDS", bid, -amount))
                    maxToSell -= abs(amount)

        #print("Total Bids: ", total_bids)
        #print("Best Bid: ", north_best_bid_amount)

        for ask, amount in reversed(order_depth.sell_orders.items()):
            if ask < south_adjusted_bid:
                if (-amount) > maxToBuy:
                    orders.append(Order("ORCHIDS", ask, maxToBuy))
                    maxToBuy = 0
                else:
                    orders.append(Order("ORCHIDS", ask, -amount))
                    maxToBuy -= abs(amount)

        orders.append(Order("ORCHIDS", round(south_adjusted_ask + 1), -maxToSell))

        orders.append(Order("ORCHIDS", round(south_adjusted_bid - 1), maxToBuy))

        #both bid and ask are higher/lower

        return orders, conversion_requests

    def basketArbitrage(self, order_depth: OrderDepth, positions, positionLimits):
        products = ["GIFT_BASKET", "CHOCOLATE", "ROSES", "STRAWBERRIES"]
        midpoints = {}
        maxToBuy = {}
        maxToSell = {}
        orders = {}
        best_bid = {}
        best_bid_amount = {}
        best_ask = {}
        best_ask_amount = {}
        hold_price = 5
        move_price = 10
        premium = 375

        # Calculate midpoints, maxToBuy, and maxToSell for each product
        for product in products:
            total_price = 0
            total_volume = 0

            # Aggregate price and volume from sell orders
            for ask, amount in order_depth[product].sell_orders.items():
                total_price += abs(ask * amount)
                total_volume += abs(amount)

            # Aggregate price and volume from buy orders
            for bid, amount in order_depth[product].buy_orders.items():
                total_price += abs(bid * amount)
                total_volume += abs(amount)

            # Calculate the weighted average price or midpoint
            midpoints[product] = total_price / total_volume

            # Calculate the maximum quantities that can be bought or sold
            maxToBuy[product] = positionLimits.get(product, 0) - positions.get(product, 0)
            maxToSell[product] = positions.get(product, 0) + positionLimits.get(product, 0)

            print(f"Product: {product}, Positition:{positions.get(product,0)}")

            best_bid[product], best_bid_amount[product] = list(order_depth[product].buy_orders.items())[0]
            best_ask[product], best_ask_amount[product] = list(order_depth[product].sell_orders.items())[0]

        # Calculate combined price of components for the basket
        combined_price = (midpoints["STRAWBERRIES"] * 6 + 
                        midpoints["CHOCOLATE"] * 4 + 
                        midpoints["ROSES"] + 
                        premium)

        #Arbitrage logic: buy components and sell basket, or buy basket and sell components
        if midpoints["GIFT_BASKET"] - combined_price > move_price:
            print("Selling basket, buying product")
            orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_bid["GIFT_BASKET"], -1*min(maxToSell["GIFT_BASKET"], abs(best_bid_amount["GIFT_BASKET"])))]
            for product in products[1:]:  # Exclude GIFT_BASKET
                if maxToBuy[product] > 0:
                    orders[product] = [Order(product, best_ask[product], min(maxToBuy[product], abs(best_ask_amount[product])))]

        elif combined_price - midpoints["GIFT_BASKET"] > move_price:
            print("Buying basket")
            orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_ask["GIFT_BASKET"], min(maxToBuy["GIFT_BASKET"], abs(best_ask_amount["GIFT_BASKET"])))]
            for product in products[1:]:  # Exclude GIFT_BASKET
                if maxToSell[product] > 0:
                    orders[product] = [Order(product, best_bid[product], -1*min(maxToSell[product], abs(best_bid_amount[product])))]

        else:
            if positions.get("GIFT_BASKET", 0) > 0 and midpoints["GIFT_BASKET"] - combined_price > hold_price:
                print("Closing Long Position (Selling Basket)")
                orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_bid["GIFT_BASKET"], -1*min(maxToSell["GIFT_BASKET"], abs(best_bid_amount["GIFT_BASKET"])))]
                for product in products[1:]:
                    if maxToBuy[product] > 0:
                        orders[product] = [Order(product, best_ask[product], min(maxToBuy[product], abs(best_ask_amount[product])))]

            elif positions.get("GIFT_BASKET", 0) < 0 and combined_price - midpoints["GIFT_BASKET"] > hold_price:
                print("Closing Short Position (Buying Basket)")
                orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_ask["GIFT_BASKET"], min(maxToBuy["GIFT_BASKET"], abs(best_ask_amount["GIFT_BASKET"])))]
                for product in products[1:]:
                    if maxToSell[product] > 0:
                        orders[product] = [Order(product, best_bid[product], -1*min(maxToSell[product], abs(best_bid_amount[product])))]
        
                
        return orders  
    
    def norm_cdf(x):
        """
        Approximate the cumulative distribution function for the standard normal distribution.
        Using the Zelen & Severo approximation.

        Parameters:
        x : float or numpy array
            Value(s) at which to evaluate the CDF

        Returns:
        float or numpy array
            CDF values corresponding to x
        """
        # Constants in the approximation formula
        p = 0.2316419
        b1 = 0.319381530
        b2 = -0.356563782
        b3 = 1.781477937
        b4 = -1.821255978
        b5 = 1.330274429
        
        t = 1 / (1 + p * np.abs(x))
        taylor_series = (b1*t + b2*t**2 + b3*t**3 + b4*t**4 + b5*t**5)
        cdf_approx = 1 - taylor_series * np.exp(-x**2 / 2) / np.sqrt(2 * np.pi)

        return np.where(x >= 0, cdf_approx, 1 - cdf_approx)
    
    def black_scholes_call(S):
        """
        Calculate the price of a European call option using the Black-Scholes formula
        with no dividend yield or risk-free rate considered.

        Parameters:
        S : float
            Current stock price (spot price)
        sigma : float
            Volatility of the stock (standard deviation of the stock's return)

        Returns:
        float
            Price of the European call option
        """
        T = 250/252 #might need to tune this
        K = 10000
        sigma = 0 #need to find this
        # Calculate d1 and d2 parameters
        d1 = (np.log(S / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Calculate the price of the call option using the custom norm_cdf function
        option_price = S * Trader.norm_cdf(d1) - K * Trader.norm_cdf(d2)
        
        return option_price

    def run(self, state: TradingState):
        POSITION_LIMITS = {'AMETHYSTS': 20, 'STARFRUIT': 20, 'ORCHIDS': 100, 'CHOCOLATE': 250, 'STRAWBERRIES': 350, 'ROSES': 60, 'GIFT_BASKET': 60}
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

        result['ORCHIDS'], conversion_requests = self.orchidArbitrage(state.order_depths['ORCHIDS'], state.position.get('ORCHIDS', 0), POSITION_LIMITS['ORCHIDS'], state.observations.conversionObservations['ORCHIDS'], state.own_trades.get('ORCHIDS', []), state.timestamp)

        #######################
        basket_orders = self.basketArbitrage(state.order_depths, state.position, POSITION_LIMITS)
        result['GIFT_BASKET'] = basket_orders.get('GIFT_BASKET', [])
        #result['CHOCOLATE'] = basket_orders.get('CHOCOLATE', [])
        #result['ROSES'] = basket_orders.get('ROSES', [])
        #result['STRAWBERRIES'] = basket_orders.get('STRAWBERRIES', [])

        traderData = {'STARFRUIT_HISTORY': starfruit_history}
        return result, conversion_requests, jsonpickle.encode(traderData)
            


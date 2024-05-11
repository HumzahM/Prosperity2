from datamodel import OrderDepth, UserId, TradingState, Order, ConversionObservation, Observation
from typing import List, Dict, Tuple
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

            #print(f"Product: {product}, Positition:{positions.get(product,0)}")

            best_bid[product], best_bid_amount[product] = list(order_depth[product].buy_orders.items())[0]
            best_ask[product], best_ask_amount[product] = list(order_depth[product].sell_orders.items())[0]

        # Calculate combined price of components for the basket
        combined_price = (midpoints["STRAWBERRIES"] * 6 + 
                        midpoints["CHOCOLATE"] * 4 + 
                        midpoints["ROSES"] + 
                        premium)

        #Arbitrage logic: buy components and sell basket, or buy basket and sell components
        if midpoints["GIFT_BASKET"] - combined_price > move_price:
            orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_bid["GIFT_BASKET"], -1*min(maxToSell["GIFT_BASKET"], abs(best_bid_amount["GIFT_BASKET"])))]

        elif combined_price - midpoints["GIFT_BASKET"] > move_price:
            orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_ask["GIFT_BASKET"], min(maxToBuy["GIFT_BASKET"], abs(best_ask_amount["GIFT_BASKET"])))]

        else:
            if positions.get("GIFT_BASKET", 0) > 0 and midpoints["GIFT_BASKET"] - combined_price > hold_price:
                orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_bid["GIFT_BASKET"], -1*min(maxToSell["GIFT_BASKET"], abs(best_bid_amount["GIFT_BASKET"])))]
            elif positions.get("GIFT_BASKET", 0) < 0 and combined_price - midpoints["GIFT_BASKET"] > hold_price:
                orders["GIFT_BASKET"] = [Order("GIFT_BASKET", best_ask["GIFT_BASKET"], min(maxToBuy["GIFT_BASKET"], abs(best_ask_amount["GIFT_BASKET"])))]
        
                
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
        sigma =  0.1562 #need to find this
        # Calculate d1 and d2 parameters
        d1 = (np.log(S / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Calculate the price of the call option using the custom norm_cdf function
        option_price = S * Trader.norm_cdf(d1) - K * Trader.norm_cdf(d2)
        
        return option_price
    
    def getFairPrice(self, product: str, order_depth: OrderDepth, own_trades: List[Order], previous_fair_price: float, informed_traders: List[str], timestamp) -> float:
        
        #print("Product: ", product)
        #print("Previous fair price: ", previous_fair_price)
        #print("Informed Traders: ", informed_traders)
        #print("Own Trades: ", own_trades)
        if(previous_fair_price == 0 or len(informed_traders) == 0 or len(own_trades) == 0):
            price = 0
            volume = 0
            for ask, amount in order_depth.sell_orders.items():
                price += abs(ask*amount)
                volume += abs(amount)
            for bid, amount in order_depth.buy_orders.items():
                price += abs(bid*amount)
                volume += abs(amount)
            if(volume != 0):
                return price / volume
            else:
                return 0
            
        else:
            last_own_trade = own_trades[-1]
            if(last_own_trade.timestamp == timestamp - 100):
                if(last_own_trade.buyer in informed_traders or last_own_trade.seller in informed_traders):
                    print("Updating fair price of ", product, " to ", last_own_trade.price, " from ", previous_fair_price)
                    return last_own_trade.price
            return previous_fair_price




    def run(self, state: TradingState):
        POSITION_LIMITS = {'AMETHYSTS': 20, 'STARFRUIT': 20, 'ORCHIDS': 100, 'CHOCOLATE': 250, 'STRAWBERRIES': 350, 'ROSES': 60, 'GIFT_BASKET': 60, 'COCONUT': 300, 'COCONUT_COUPON': 600}
        BID_ASK_SPREADS = {'AMETHYSTS': 3, 'STARFRUIT': 1.9, 'COCONUT': 1, 'COCONUT_COUPON':10} #half of spread
        INFORMED_TRADERS = {'STARFRUIT': ['Remy', 'Vinnie', 'Ruby', 'Vladimir', 'Rhianna'], 'ROSES': ['Vladimir'], 'CHOCOLATE': ['Remy', 'Vladimir'], 'STRAWBERRIES': ['Vladimir'], 'GIFT_BASKET': ['Rhianna', 'Ruby'], 'COCONUT_COUPON': ['Vinnie', 'Rhianna'], 'COCONUT': ['Raj', 'Rhianna']}
        result = {}
        #######################
        #Amethysts
        #######################
        result['AMETHYSTS'] = self.ordersSimpleMarketMaking('AMETHYSTS', state.order_depths['AMETHYSTS'], state.position.get('AMETHYSTS', 0), POSITION_LIMITS['AMETHYSTS'], 10000, BID_ASK_SPREADS['AMETHYSTS'])

        #######################
        #Starfruit
        #######################

        fair_prices = {'AMETHYSTS': 10000, 'STARFRUIT': 0, 'CHOCOLATE': 0, 'STRAWBERRIES': 0, 'ROSES': 0, 'GIFT_BASKET': 0, 'COCONUT': 0, 'COCONUT_COUPON': 0}
        if state.traderData:
            try:
                fair_prices = jsonpickle.decode(state.traderData)
            except Exception as e:
                print(f"Error decoding traderData: {e}")
                # Handle the exception appropriately, maybe log it or set a default value
                # For this example, decoded_data remains an empty dictionary

        for product in fair_prices:
            fair_prices[product] = self.getFairPrice(product, state.order_depths[product], state.own_trades.get(product, []), fair_prices[product], INFORMED_TRADERS.get(product, []), state.timestamp)
            if(fair_prices[product] != 0):
                result[product] = self.ordersSimpleMarketMaking(product, state.order_depths[product], state.position.get(product, 0), POSITION_LIMITS[product], fair_prices[product], BID_ASK_SPREADS.get(product, 2))

        #######################
        #Orchids
        #######################

        result['ORCHIDS'], conversion_requests = self.orchidArbitrage(state.order_depths['ORCHIDS'], state.position.get('ORCHIDS', 0), POSITION_LIMITS['ORCHIDS'], state.observations.conversionObservations['ORCHIDS'], state.own_trades.get('ORCHIDS', []), state.timestamp)

        #######################
        basket_orders = self.basketArbitrage(state.order_depths, state.position, POSITION_LIMITS)
        #result['GIFT_BASKET'] = basket_orders.get('GIFT_BASKET', [])
        
        coconut_best_bid, coconut_best_bid_amount = list(state.order_depths['COCONUT'].buy_orders.items())[0]
        coconut_best_ask, coconut_best_ask_amount = list(state.order_depths['COCONUT'].sell_orders.items())[0]
        coconut_midpoint = (coconut_best_bid + coconut_best_ask) / 2

        coupon_best_bid, coupon_best_bid_amount = list(state.order_depths['COCONUT_COUPON'].buy_orders.items())[0]
        coupon_best_ask, coupon_best_ask_amount = list(state.order_depths['COCONUT_COUPON'].sell_orders.items())[0]
        coupon_midpoint = (coupon_best_bid + coupon_best_ask) / 2

        #coupon_fair_price = (Trader.black_scholes_call(coconut_midpoint) + coupon_midpoint) / 2
        coupon_fair_price = Trader.black_scholes_call(coconut_midpoint)
        #print("Coupon Midpoint: ", coupon_midpoint)
        #print("Black Scholes Call: ", Trader.black_scholes_call(coconut_midpoint))

        #result['COCONUT_COUPON'] = self.ordersSimpleMarketMaking('COCONUT_COUPON', state.order_depths['COCONUT_COUPON'], state.position.get('COCONUT_COUPON', 0), POSITION_LIMITS['COCONUT_COUPON'], coupon_fair_price, BID_ASK_SPREADS['COCONUT_COUPON'])
        #result['COCONUT'] = self.ordersSimpleMarketMaking('COCONUT', state.order_depths['COCONUT'], state.position.get('COCONUT', 0), POSITION_LIMITS['COCONUT'], coconut_midpoint, BID_ASK_SPREADS['COCONUT'])

        #traderData = any dictionary we want to save for the next run
        
        return result, conversion_requests, jsonpickle.encode(fair_prices)
            


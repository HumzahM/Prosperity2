def cdf(x):
    return (1/10000)*(x*x) #at x = 100 cdf = 1

#bid1 goes from 0 to 99
#bid2 goes from 1 to 100
#avg goes from 1 to 100
def profit (bid1, bid2, avg):
    if(bid1 >= bid2):
        p = 0
        print("Error: bid1 should be less than bid2")
    if(bid2 < avg):
        p = (100-bid1)*cdf(bid1) + (100-bid2)*(cdf(bid2)-cdf(bid1))*((1000-(avg+900))/(1000-(bid2+900)))
    else:
        p = (100-bid1)*cdf(bid1) + (100-bid2)*(cdf(bid2)-cdf(bid1))
    return p

import numpy as np
import matplotlib.pyplot as plt

# Range of avg values from 0 to 100
avg_values = range(75, 100)

# Storage for optimal bids
optimal_bid1 = []
optimal_bid2 = []
max_profits = []

# Determine optimal bids for each avg value
for avg in avg_values:
    max_profit = float('-inf')
    best_bid1, best_bid2 = 0, 0
    
    for bid1 in range(0, 99):
        for bid2 in range(bid1 + 1, 99):
            current_profit = profit(bid1, bid2, avg)
            if current_profit > max_profit:
                max_profit = current_profit
                best_bid1, best_bid2 = bid1, bid2

    max_profits.append(max_profit)
    optimal_bid1.append(best_bid1)
    optimal_bid2.append(best_bid2)

# Plotting the updated results with max profit on a secondary y-axis

fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(range(75, 100), optimal_bid1, label='Optimal bid1')
ax1.plot(range(75, 100), optimal_bid2, label='Optimal bid2')
ax1.set_xlabel('Average (avg)')
ax1.set_ylabel('Bids (bid1 and bid2)')
ax1.legend(loc='upper left')
ax1.grid(True)
ax2 = ax1.twinx()
ax2.plot(range(75, 100), max_profits, label='Max Profit', color='green', linestyle=':')
ax2.set_ylim(0, 21)
ax2.set_ylabel('Max Profit')
ax2.legend(loc='upper right')
plt.title('Optimal Bids and Max Profit for Different Average Values with Adjusted bid2 Range')
plt.show()
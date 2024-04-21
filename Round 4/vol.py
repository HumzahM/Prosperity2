import pandas as pd
import numpy as np

file_paths = [
    'prices_round_4_day_1.csv',
    'prices_round_4_day_2.csv',
    'prices_round_4_day_3.csv'
]
dataframes = []
for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path, delimiter=";")
    # Adjust timestamps
    df['timestamp'] += i * 1000000
    dataframes.append(df)

combined_df = pd.concat(dataframes)

main_df = combined_df[combined_df['product'] == 'COCONUT'][['timestamp', 'mid_price']]
main_df['log_returns'] = np.log(main_df['mid_price'] / main_df['mid_price'].shift(1))
print(main_df)
# Step 2: Calculate Volatility (standard deviation of log returns)
volatility = main_df['log_returns'].std()

# Step 2: Annualize the volatility
total_target_samples_per_year = 252 * 10000  # Total number of data points in a standard trading year
total_samples_in_data = 30000  # Total samples in your data

annualized_volatility = volatility * np.sqrt(total_target_samples_per_year / total_samples_in_data)

# Print the annualized volatility
print("Annualized Volatility: ", annualized_volatility)
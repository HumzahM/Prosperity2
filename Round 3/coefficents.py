import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Load the CSV files
file_paths = [
    'prices_round_3_day_0.csv',
    'prices_round_3_day_1.csv',
    'prices_round_3_day_2.csv'
]
dataframes = []
for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path, delimiter=";")
    # Adjust timestamps
    df['timestamp'] += i * 1000000
    dataframes.append(df)

# Combine all data into a single DataFrame
combined_df = pd.concat(dataframes)

# Filter for the specific products
products = ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']
pivot_dfs = []
for product in products:
    temp_df = combined_df[combined_df['product'] == product][['timestamp', 'mid_price']]
    temp_df = temp_df.rename(columns={'mid_price': product})
    pivot_dfs.append(temp_df)

# Merge all product dataframes on 'timestamp'
from functools import reduce
merged_df = reduce(lambda left, right: pd.merge(left, right, on='timestamp', how='inner'), pivot_dfs)

# Linear Regression Model
X = merged_df[['CHOCOLATE', 'STRAWBERRIES', 'ROSES']]  # Use A, B, C as independent predictors
y = merged_df['GIFT_BASKET']  # Response variable
model = LinearRegression()
model.fit(X, y)

# Coefficients, rounded to nearest integer
alpha = model.intercept_
beta_A = model.coef_[0]
beta_B = model.coef_[1]
beta_C = model.coef_[2]

print("First Estimates: ")
print(f"Estimated Alpha: {alpha}, Estimated Beta for A: {beta_A}, Beta for B: {beta_B}, Beta for C: {beta_C}")

beta_A = int(round(beta_A))
beta_B = int(round(beta_B))
beta_C = int(round(beta_C))

fixed_contributions = beta_A * merged_df['CHOCOLATE'] + beta_B * merged_df['STRAWBERRIES'] + beta_C * merged_df['ROSES']

# Re-run regression to optimize alpha with fixed beta coefficients
model_alpha = LinearRegression(fit_intercept=True)
model_alpha.fit(np.ones((len(fixed_contributions), 1)), y - fixed_contributions)

# Coefficient for alpha (intercept)
optimal_alpha = int(round(model_alpha.intercept_))

print("With rounded coefficents: ")
print(f"Optimal Alpha: {optimal_alpha}")

optimal_alpha = 375
predicted_prices = beta_A * merged_df['CHOCOLATE'] + beta_B * merged_df['STRAWBERRIES'] + beta_C * merged_df['ROSES'] + optimal_alpha
actual_prices = merged_df['GIFT_BASKET']

# Function to calculate Mean Squared Error (MSE) at different lags
def calculate_mse_at_lag(actual, predicted, lag):
    if lag == 0:
        return np.mean((actual - predicted) ** 2)
    else:
        # Ensure predicted is not shorter than actual after lagging
        return np.mean((actual[lag:] - predicted[:-lag]) ** 2)

# Analyzing lags from 0 to 100 (inclusive)
lag_range = range(0, 101)
mse_results = [calculate_mse_at_lag(actual_prices, predicted_prices, lag) for lag in lag_range]

# Plotting the MSE results
plt.figure(figsize=(10, 5))
plt.plot(lag_range, mse_results, marker='o', linestyle='-', color='b')
plt.title('MSE vs. Lag')
plt.xlabel('Lag')
plt.ylabel('Mean Squared Error')
plt.grid(True)
plt.show()

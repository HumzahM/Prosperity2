from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np

# Sample data
data = np.genfromtxt('midpoint.csv')

# Prepare the dataset
def find_best_n(n):
    X = []
    y = []
    for i in range(len(data) - n):
        X.append(data[i:i+n])
        y.append(data[i+n])

    X = np.array(X)
    y = np.array(y)

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the linear regression model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    score = model.coef_
    r_sq = model.score(X_test, y_test)
    intercept = model.intercept_
    print("Coefficients:", score)
    print("Intercept:", intercept)
    print("R^2:", r_sq)
    return r_sq

# Now you can use model.predict() to predict the next value given the last n values

# Find the best n
best_n = 0
best_r_sq = 0

for i in range(1, 10):
    rq = find_best_n(i)
    if rq > best_r_sq:
        best_r_sq = rq
        best_n = i

print("Best n:", best_n)
print("Best R^2:", best_r_sq)


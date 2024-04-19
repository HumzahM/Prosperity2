import numpy as np

# Constants
base_treasure = 7500

def calculate_expected_values(treasure_multipliers, hunters, player_distribution, base_treasure):
    # Validate and scale player_distribution matrix to sum to 100 if necessary
    player_distribution_sum = player_distribution.sum()
    if player_distribution_sum == 0:
        return "Error: Player distribution matrix cannot be all zeros."
    elif player_distribution_sum != 100:
        print("Scaling player distribution matrix to sum to 100.")
        print("Original sum: " + str(player_distribution_sum))
        player_distribution = (player_distribution / player_distribution_sum) * 100

    # Calculate the expected value for each spot
    total_hunters = hunters + (player_distribution / 100)
    total_treasure = treasure_multipliers * base_treasure
    expected_values = total_treasure / total_hunters
    expected_values = np.rint(expected_values).astype(int)

    return expected_values

# Input your data here
treasure_multipliers = np.array([
    [24, 70, 41, 21, 60],
    [47, 82, 87, 80, 35],
    [73, 89, 100, 90, 17],
    [77, 83, 85, 79, 55],
    [12, 27, 52, 15, 30]
])

hunters = np.array([
    [2, 4, 3, 2, 4],
    [3, 5, 5, 5, 3],
    [4, 5, 8, 7, 2],
    [5, 5, 5, 5, 4],
    [2, 3, 4, 2, 3]
])

#This one is all estimates. If I estimate correctly, I will get the highest EV

player_distribution = np.array([
    [3, 5, 4, 3, 5],
    [4, 7, 8, 7, 5],
    [6, 8, 10, 8, 2],
    [6, 8, 8, 6, 4],
    [4, 2, 5, 3, 5]
])

# Calculate EV
expected_values = calculate_expected_values(treasure_multipliers, hunters, player_distribution, base_treasure)
for row in expected_values:
    print(row)
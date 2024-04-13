matrix = [[1, 0.48, 1.52, 0.71],
          [2.05, 1, 3.26, 1.56],
          [0.64, 0.3, 1, 0.46],
          [1.41, 0.61, 2.08, 1]]

#from is i, to is j

def recursiveMax(stepsLeft, i, value, path):
    if stepsLeft == 0:
        if i == 3:
            return (value, path + [(3, i)])  # Include final position in path
        else:
            return (-1, [])  # Return empty path for invalid end
    else:
        max_value = -1
        best_path = []
        for j in range(4):
            current_value, current_path = recursiveMax(stepsLeft - 1, j, value * matrix[i][j], path + [(i, j)])
            if current_value > max_value:
                max_value = current_value
                best_path = current_path
        return (max_value, best_path)

# Start from the bottom row (index 3), initial value is 1, empty path initially
result_value, result_path = recursiveMax(5, 3, 1, [])
print("Maximum Value:", result_value)
print("Path:", result_path)
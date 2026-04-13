import numpy as np
import matplotlib.pyplot as plt

# Create bailout probabilities array
bailout_probabilities = np.linspace(0, 1, 100)

# Define desired trust level values
start_trust_level = 0.43
peak_trust_level = 0.68
end_trust_level = 0.57

def piecewise_trust_function(bailout_prob):
    # Define the bailout probability where peak trust level occurs
    peak_bailout_prob = 0.65
    
    if bailout_prob < peak_bailout_prob:
        # Increase linearly to the peak
        return ((peak_trust_level - start_trust_level) / peak_bailout_prob) * bailout_prob + start_trust_level
    else:
        # Decrease linearly after the peak
        return ((end_trust_level - peak_trust_level) / (1 - peak_bailout_prob)) * (bailout_prob - 1) + end_trust_level

# Apply the piecewise function to generate the base trust levels
base_trust_levels = np.array([piecewise_trust_function(prob) for prob in bailout_probabilities])

# Generate random spikes
random_spikes = np.random.normal(0, 0.01, size=bailout_probabilities.shape)  # Small random noise

# Apply the random spikes to the trust levels
spiky_trust_levels = base_trust_levels + random_spikes

# Plotting the results
plt.figure(figsize=(15, 7))
#plt.plot(bailout_probabilities, base_trust_levels, label='Base Trust Levels', color='blue')
plt.plot(bailout_probabilities, spiky_trust_levels, label='Average Trust Levels', color='red')
plt.xlabel('Bailout Probability')
plt.ylabel('Customer Trust Level')
plt.ylim(0, 1)
plt.xlim(0, 1)  
plt.title('Trust Levels vs. Bailout Probabilities')
plt.legend()
plt.grid()
plt.show()

import networkx as nx
import matplotlib.pyplot as plt

class bank_network:
    pass

def create_bank_network(grid_size, rewiring_probability, num_nodes, power_law_exponent):
    # Create a 2D spatial grid with periodic boundary conditions
    grid_network = nx.grid_2d_graph(grid_size, grid_size, periodic=True)
    
    # Create a small world network by rewiring edges 
    small_world_network = nx.watts_strogatz_graph(num_nodes, k=4, p=rewiring_probability)
    
    # Create a power law degree distribution network using Barabási-Albert model
    power_law_network = nx.barabasi_albert_graph(num_nodes, m=2)
    
    return grid_network, small_world_network, power_law_network

# Example usage:
grid_size = 10
rewire_prob = 0.2
num_nodes = 100
powerlaw_exponent = 2.5

grid_network, small_world_network, power_law_network = create_bank_network(grid_size, rewire_prob, num_nodes, powerlaw_exponent)

# Visualize the networks using matplotlib
plt.figure(figsize=(12, 4))

plt.subplot(131)
nx.draw(grid_network, with_labels=False, node_size=10)
plt.title('2D Spatial Grid Network')

plt.subplot(132)
nx.draw(small_world_network, with_labels=False, node_size=10)
plt.title('Small World Network')

plt.subplot(133)
nx.draw(power_law_network, with_labels=False, node_size=10)
plt.title('Power Law Network')

plt.tight_layout()
plt.show()

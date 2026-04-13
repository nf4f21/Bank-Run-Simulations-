from collections import Counter
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random
import seaborn as sns
from bank import Bank
from financial_manager import FinancialManager

financial_manager = FinancialManager()
# Create a 2D spatial grid with periodic boundary conditions
def create_bank_network(grid_size, rewiring_probability, num_nodes, powerlaw_exponent):
    # Create a 2D spatial grid with periodic boundary conditions
    grid_network = nx.grid_2d_graph(grid_size, grid_size, periodic=True)
    
    # Create a small world network by rewiring edges
    small_world_network = nx.watts_strogatz_graph(num_nodes, k=4, p=rewiring_probability)
    
    # Create a power law degree distribution network using Barabási-Albert model
    power_law_network = nx.barabasi_albert_graph(num_nodes, m=2)

    for network in (grid_network, small_world_network, power_law_network):
        for node in network.nodes:
            network.nodes[node]['bank'] = Bank(risk_strategy=random.random(),financial_manager=financial_manager,network_degree=network.degree(node),tau=0.1)
    
    return grid_network, small_world_network, power_law_network

def compute_network_metrics(network):
    # Compute average path length
    try:
        avg_path_length = nx.average_shortest_path_length(network)
    except nx.NetworkXError:  # Handle for disconnected graphs
        avg_path_length = float('inf')
    
    # Compute clustering coefficient
    clustering_coefficient = nx.average_clustering(network)
    
    return avg_path_length, clustering_coefficient

def adapt_strategy(network,sigma=0.01, pmut=0.0005):
    print("Adapting strategy operation commencing")
    #adapts the strategy of banks based on comparison with other banks, inclduing a mutaiton step
    for node in network.nodes:
        bank_i = network.nodes[node]['bank']
        #select a peer for comaparison 
        #peers = list(network.nodes)
        degree_i = network.degree(node)
        #Select a peer for comparison within ±30% of the degree of the bank
        peers = [peer for peer in network.nodes if degree_i * 0.7 <= network.degree(peer) <= degree_i * 1.3]

        if peers:
            peer_node = random.choice(peers)
            bank_j = network.nodes[peer_node]['bank']

            #adapt the strategy of bank i based on bank j
            if bank_j.calculate_profit() > bank_i.calculate_profit():
                bank_i.risk_strategy += sigma * (bank_j.risk_strategy - bank_i.risk_strategy)

        #mutation 
        bank_i.risk_strategy += np.random.uniform(-pmut, pmut)
        bank_i.risk_strategy = min(max(bank_i.risk_strategy, 0), 1)
    
    print(f"Bank {node} is adapting its strategy based on Bank {peer_node}'s strategy")
    print(f"Bank {node} new strategy: {bank_i.risk_strategy}")


def contagion_of_distress(network, cascade_tracker,eta ,mu=0.01):
    print("Contagion of distress operation commencing")
    #simulates the contagion of distress from bankrupt bank to their neibours 
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        if bank.isBankrupt:
            #start tracking a new cascade
            cascade_id = len(cascade_tracker) + 1
            cascade_size = 1
            cascade_tracker[cascade_id] = cascade_size
            propagate_shock(network, node, eta, cascade_tracker, cascade_id, mu)
            for neighbor in network.neighbors(node):
                neighbor_bank = network.nodes[neighbor]['bank']
                if not neighbor_bank.isBankrupt and random.random() < mu:
                    neighbor_bank.update_insolvency()
                    print(f"Bank {neighbor} is affected by contagion from Bank {node}")
                    print(f"Bank {neighbor} has become insolvent due to contagion from Bank {node}")
                    

    


def systemic_shock(network, eta, p0, xi):
    print("Systemic shock operation commencing")
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        if random.random() < p0:  # External fluctuation occurs
            if random.random() < bank.risk_strategy:  # Bank becomes insolvent
                if random.random() < xi:  # Bank becomes bankrupt
                    bank.update_insolvency()
                   # propagate_shock(network, node, eta)  # Propagate shock if bank becomes bankrupt

def size_based_bailout(network, k_threshold, financial_manager):
    print("Size-based bailout operation commencing")
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        bank_size = network.degree(node)
        if bank.isInsolvent and network.degree(node) > k_threshold:  #netowrk.degree(node) gives the degree of the node which is the number of connections of the node
            bank.isBankrupt = False # the bank is bailed out
            bank.isInsolvent = False # the bank is no longer insolvent
            print(f"bank {node} is bailed out (sized-base), Size: {bank_size}, Threshold: {k_threshold} ")
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        risk_strategy = bank.risk_strategy
        if network.degree(node) >k_threshold:
            assert not bank.isBankrupt, "Size-based bailout failed for bank {node} with degree {network.degree(node)} for a bank that should have been bailed out."
    financial_manager.update_for_bailout(bank)
    print(f"Bailout (size-based) for bank at node {node} with balance sheet size: {bank.balance_sheet_size}")


def neighbor_based_bailout(network, c0, c1, theta):
    print("Neighbor-based bailout operation commencing")
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        if bank.isInsolvent:
            bank_size = network.degree(node)
            bailout_probability = c0 + c1 * (bank_size ** (-theta))
            if np.random.uniform() < bailout_probability:
                bank.isBankrupt = False # the bank is bailed out    
                bank.isInsolvent = False # the bank is no longer insolvent
                print(f"bank {node} is bailed out (neibor-based), Size: {bank_size}, Bailout Probability: {bailout_probability:.2f}")
    

def apply_bankruptcy(network,financial_manager):
    print("Applying bankruptcy to banks")
    for node in network.nodes:  # Corrected typo here from 'modes' to 'nodes'
        bank = network.nodes[node]['bank']
        if bank.isInsolvent:
            bank.update_bankruptcy()
            #update the financial manager for the bankruptcy
            risk_strategy = bank.risk_strategy
            financial_manager.update_for_bankruptcy(bank)
            print(f"Bank {node} has been marked as bankrupt post-bailout.")
            print(f"Bankruptcy updated for bank at node {node} with balance sheet size: {bank.balance_sheet_size}")

def propagate_shock(network, node, eta, cascade_tracker, cascade_id, mu):
    print("Propagating shock operation commencing")
    #propagate shock to the neighbors of the bankrupt bank
    for neighbor in network.neighbors(node):
        neighbor_bank = network.nodes[neighbor]['bank']
        k = len(list(network.neighbors(neighbor)))  # degree of the bank which gives the number of neibours of the bank
        if neighbor_bank.isInsolvent:
            continue # if the neibour bank is already insolvent, then no need to propagate the shock
        
        shock_probability = min(eta/k, 1) # the shock probability is the maximum of eta/k and 0.1
        if random.random() < shock_probability:
            neighbor_bank.update_insolvency()
            propagate_shock(network, neighbor, eta, cascade_tracker, cascade_id, mu) #propagate the shock to the neibours of the neibour bank, recursively propagate the shock to the neibours of the neibour bank recursively
        else:
            neighbor_bank.adjust_risk_strategy(eta, k) # adjust the risk strategy of the neibour bank

        if not neighbor_bank.isBankrupt and random.random() < mu:
            neighbor_bank.update_insolvency()
            neighbor_bank.isBankrupt = True  # Assuming this marks the bank as bankrupt
            cascade_tracker[cascade_id] += 1
            propagate_shock(network, neighbor, eta, cascade_tracker, cascade_id, mu)

      


#we now need to capture the state of the network  before and after the shock
            
def capture_network_state(network):
    insolvent_banks = 0
    bankrupt_banks = 0
    total_risk_strategy = 0
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        if bank.isInsolvent:
            insolvent_banks += 1
        if bank.isBankrupt:
            bankrupt_banks += 1
        total_risk_strategy += bank.risk_strategy
    average_risk_strategy = total_risk_strategy/network.number_of_nodes()
    return{
        'insolvent_banks': insolvent_banks,
        'bankrupt_banks': bankrupt_banks,
        'average_risk_strategy': average_risk_strategy
    }


def visualize_network_state(network):
    pos = nx.spring_layout(network)  # or any other layout
    risk_strategies = [network.nodes[node]['bank'].risk_strategy for node in network.nodes]
    nx.draw(network, pos, node_color=risk_strategies, with_labels=True, cmap=plt.cm.Blues)
    plt.show()

def propagate_shock_after_bailout(network, eta,cascade_tracker, mu=0.01):
            for node in network.nodes:
                bank = network.nodes[node]['bank']
                #only propagate the shocks for banks that are still insolvent and not bailed out 
                if bank.isInsolvent and not bank.isBankrupt:
                    cascade_id = len(cascade_tracker) + 1
                    cascade_tracker[cascade_id] = 1  # Initialize the cascade size
                    propagate_shock(network, node, eta, cascade_tracker, cascade_id, mu)


def update_balance_sheets_for_network(network):
    print("Updating balance sheets for banks in the network")
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        network_degree = network.degree(node)
        bank.update_balance_sheet_size(network_degree)
        print(f"Balance sheet updated for bank at node {node} with balance sheet size: {bank.balance_sheet_size}")

def update_benefits_for_network(network,financial_manager):
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        financial_manager.update_for_benefit(bank)
        print(f"Benefit updated for bank at node {node} with balance sheet size: {bank.balance_sheet_size}")

def update_asset_write_downs_for_network(network,financial_manager):
    for node in network.nodes:
        bank=network.nodes[node]['bank']
        if bank.isInsolvent:
            financial_manager.update_for_asset_write_down(bank)
            print(f"Asset write down updated for bank at node {node} with balance sheet size: {bank.balance_sheet_size}")

def logarithimic_binning(counter, bin_factor=1.3):
     # Find the log-binned frequencies
    max_size = max(counter.keys())
    bins = np.logspace(np.log10(1), np.log10(max_size), num=int(np.log10(max_size) / np.log10(bin_factor)) + 1)
    binned_frequencies = np.histogram(list(counter.keys()), bins=bins, weights=list(counter.values()))[0]
    binned_sizes = (bins[:-1] + bins[1:]) / 2
    return binned_sizes, binned_frequencies

    


def run_simulation(grid_size, rewire_prob, num_nodes, powerlaw_exponent, eta, p0, xi, k_threshold, c0, c1, theta, num_timesteps):
    combined_social_costs = []  # To store combined social costs for each run
    #financial_manager = FinancialManager()
    
    time_steps = []  # To store the timesteps for each run

    # Initialize containers for collecting data across runs
    avg_risk_strategy_runs_grid = []
    avg_risk_strategy_runs_small_world = []
    avg_risk_strategy_runs_power_law = []
    insolvent_banks_runs_grid = []
    insolvent_banks_runs_small_world = []
    insolvent_banks_runs_power_law = []
    bankrupt_banks_runs_grid = []
    bankrupt_banks_runs_small_world = []
    bankrupt_banks_runs_power_law = []

    # New dictionary to track cascade sizes
    cascade_tracker_grid = {}
    cascade_tracker_small_world = {}
    cascade_tracker_power_law = {}


    for time_step in range(num_timesteps):
        # Initialize separate FinancialManager instances for each network type at the beginning of each run
        fm_grid = FinancialManager()
        fm_small_world = FinancialManager()
        fm_power_law = FinancialManager()

        time_steps.append(time_step)
    

        # Step 1: Create the networks
        grid_network, small_world_network, power_law_network = create_bank_network(grid_size, rewire_prob, num_nodes, powerlaw_exponent)

        # Initial balance sheet size update
        for network in [grid_network, small_world_network, power_law_network]:
            for node, data in network.nodes(data=True):
                bank = data['bank']
                network_degree = network.degree(node)
                bank.update_balance_sheet_size(network_degree)  # Update each bank's balance sheet size


        # Step 2: Capture initial state
        initial_states = {
            'grid': capture_network_state(grid_network),
            'small_world': capture_network_state(small_world_network),
            'power_law': capture_network_state(power_law_network),
        }   

        # Apply systemic shocks, bailout mechanisms, and propagate shock after bailout
        systemic_shock(grid_network, eta, p0, xi)
        update_balance_sheets_for_network(grid_network)
        systemic_shock(small_world_network, eta, p0, xi)
        update_balance_sheets_for_network(small_world_network)
        systemic_shock(power_law_network, eta, p0, xi)
        update_balance_sheets_for_network(power_law_network)

        # Step 4: Capture initial state
        systemic_shock_states = {
            'grid': capture_network_state(grid_network),
            'small_world': capture_network_state(small_world_network),
            'power_law': capture_network_state(power_law_network),
        }

        


        size_based_bailout(grid_network, k_threshold,fm_grid)
        update_balance_sheets_for_network(grid_network)
        size_based_bailout(small_world_network, k_threshold,fm_small_world)
        size_based_bailout(power_law_network, k_threshold,fm_power_law)

        neighbor_based_bailout(grid_network, c0, c1, theta)
        update_balance_sheets_for_network(grid_network)
        neighbor_based_bailout(small_world_network, c0, c1, theta)
        neighbor_based_bailout(power_law_network, c0, c1, theta)

        apply_bankruptcy(grid_network,fm_grid)
        update_balance_sheets_for_network(grid_network)
        apply_bankruptcy(small_world_network,fm_small_world)
        apply_bankruptcy(power_law_network,fm_power_law)

        propagate_shock_after_bailout(grid_network, eta, cascade_tracker_grid)
        propagate_shock_after_bailout(small_world_network, eta, cascade_tracker_small_world)
        propagate_shock_after_bailout(power_law_network, eta, cascade_tracker_power_law)

        # Step 7: Capture post-shock state
        post_shock_states = {
            'grid': capture_network_state(grid_network),
            'small_world': capture_network_state(small_world_network),
            'power_law': capture_network_state(power_law_network),
        }

        adapt_strategy(grid_network)
        update_balance_sheets_for_network(grid_network)
        update_benefits_for_network(grid_network,fm_grid)
        adapt_strategy(small_world_network)
        update_balance_sheets_for_network(small_world_network)
        update_benefits_for_network(small_world_network,fm_small_world)
        adapt_strategy(power_law_network)
        update_balance_sheets_for_network(power_law_network)
        update_benefits_for_network(power_law_network,fm_power_law)

        contagion_of_distress(grid_network, cascade_tracker_grid,eta, mu=0.01)
        update_balance_sheets_for_network(grid_network)
        update_asset_write_downs_for_network(grid_network,fm_grid)
        contagion_of_distress(small_world_network, cascade_tracker_small_world,eta, mu=0.01)
        update_balance_sheets_for_network(small_world_network)
        update_asset_write_downs_for_network(small_world_network,fm_small_world)
        contagion_of_distress(power_law_network, cascade_tracker_small_world,eta, mu=0.01)
        update_balance_sheets_for_network(power_law_network)
        update_asset_write_downs_for_network(power_law_network,fm_power_law)



        # Calculate individual social costs
        U_Psi_grid = fm_grid.calculate_social_cost()
        U_Psi_small_world = fm_small_world.calculate_social_cost()
        U_Psi_power_law = fm_power_law.calculate_social_cost()

        # Calculate the combined social cost for the run
        combined_U_Psi = U_Psi_grid + U_Psi_small_world + U_Psi_power_law
        combined_social_costs.append(combined_U_Psi)

        # Print the combined social cost for the run
        print(f"Run {time_step+1} - Combined Social Cost: {combined_U_Psi}")


        # Print individual social costs for analysis
        print(f"Run {time_step+1} - Social Cost for Grid Network: {U_Psi_grid}")
        print(f"Run {time_step+1} - Social Cost for Small-World Network: {U_Psi_small_world}")
        print(f"Run {time_step+1} - Social Cost for Power-Law Network: {U_Psi_power_law}")


        current_state = capture_network_state(grid_network)
        #time_steps.append(time_step)
       # avg_risk_strategy_runs.append(current_state['average_risk_strategy'])
        #bankrupt_banks_runs.append(current_state['bankrupt_banks'])




        #print out the current state at certain intervals 
        if time_step % 100 == 0:
            print(f"Time step {time_step}: Avg. Risk Strategy: current_state['average_risk_strategy'], Bankrupt Banks: current_state['bankrupt_banks']")   

        addtional_strategy_states = {
        'grid': capture_network_state(grid_network),
        'small_world': capture_network_state(small_world_network),
        'power_law': capture_network_state(power_law_network),
        }

        

        # Step 8: Analyze and print results
        for network_type in initial_states.keys():
            print(f"{network_type} Network - Initial State: {initial_states[network_type]}")
            print(f"{network_type} Network - Systemic-Shock State: {systemic_shock_states[network_type]}")
            print(f"{network_type} Network - Post-Shock State: {post_shock_states[network_type]}")
            print(f"{network_type} Network - Additional Strategy State: {addtional_strategy_states[network_type]}")
            print()  # Just for better readability of the output


        # Collect data from this run
        post_shock_state_grid = capture_network_state(grid_network)
        post_shock_state_small_world = capture_network_state(small_world_network)
        post_shock_state_power_law = capture_network_state(power_law_network)

        avg_risk_strategy_runs_grid.append(post_shock_state_grid['average_risk_strategy'])
        avg_risk_strategy_runs_small_world.append(post_shock_state_small_world['average_risk_strategy'])
        avg_risk_strategy_runs_power_law.append(post_shock_state_power_law['average_risk_strategy'])

        insolvent_banks_runs_grid.append(post_shock_state_grid['insolvent_banks'])
        insolvent_banks_runs_small_world.append(post_shock_state_small_world['insolvent_banks'])
        insolvent_banks_runs_power_law.append(post_shock_state_power_law['insolvent_banks'])

        bankrupt_banks_runs_grid.append(post_shock_state_grid['bankrupt_banks'])
        bankrupt_banks_runs_small_world.append(post_shock_state_small_world['bankrupt_banks'])
        bankrupt_banks_runs_power_law.append(post_shock_state_power_law['bankrupt_banks'])

        cascade_sizes_grid = Counter(cascade_tracker_grid.values())
        cascade_sizes_small_world = Counter(cascade_tracker_small_world.values())


        # At the end of your function, return the collected data
    return time_steps, avg_risk_strategy_runs_grid, avg_risk_strategy_runs_small_world, bankrupt_banks_runs_grid, bankrupt_banks_runs_small_world,cascade_sizes_grid, cascade_sizes_small_world

    

def analyze_data(avg_risk_strategy_runs_grid, avg_risk_strategy_runs_small_world, avg_risk_strategy_runs_power_law, insolvent_banks_runs_grid,insolvent_banks_runs_small_world,insolvent_banks_runs_power_law, bankrupt_banks_runs_grid, bankrupt_banks_runs_small_world, bankrupt_banks_runs_power_law,U_Psi):
    # Example analysis: Print average values
    print(f"Average Risk Strategy: {np.mean(avg_risk_strategy_runs_grid)}")
    print(f"Average Number of Insolvent Banks: {np.mean(insolvent_banks_runs_grid)}")
    print(f"Average Number of Bankrupt Banks: {np.mean(bankrupt_banks_runs_grid)}")
    print(f"Social Cost U(Ψ) for this simulation run: {U_Psi}")

    # Example visualization: Histograms of collected data
    plt.figure(figsize=(15, 5))
    plt.subplot(1, 3, 1)
    plt.hist(avg_risk_strategy_runs_grid, bins=10, color='blue')
    plt.title('Average Risk Strategy')
    plt.xlabel('Average Risk Strategy (Unitless)')
    plt.ylabel('Frequency')

    plt.subplot(1, 3, 2)
    plt.hist(insolvent_banks_runs_grid, bins=10, color='orange')
    plt.title('Insolvent Banks')
    plt.xlabel('Number of Insolvent Banks')
    plt.ylabel('Frequency')
    

    plt.subplot(1, 3, 3)
    plt.hist(bankrupt_banks_runs_grid, bins=10, color='green')
    plt.title('Bankrupt Banks')
    plt.xlabel('Number of Bankrupt Banks')
    plt.ylabel('Frequency')
    plt.show()
# After all runs, analyze and visualize the collected data
    analyze_data(avg_risk_strategy_runs_grid, insolvent_banks_runs_grid, bankrupt_banks_runs_grid,U_Psi=financial_manager.calculate_social_cost())

# Example call to the simulation loop method
time_steps, avg_risk_strategy_runs_grid,avg_risk_strategy_runs_small_world,bankrupt_banks_runs_grid,bankrupt_banks_runs_small_world, cascade_sizes_grid,cascade_sizes_small_world= run_simulation(
    grid_size=10000,  # Size of one side of the square grid for the 2D grid network.
    rewire_prob=0.2,  # Probability of rewiring each edge in the small-world network creation process.
    num_nodes=100000,  # Total number of nodes (banks) in the network.
    powerlaw_exponent=2.5,  # Exponent parameter for the power-law distribution in the network degree distribution.
    eta=0.5,  # Parameter related to the shock propagation mechanism, possibly affecting the severity or reach of contagion effects. (IN MY CASE η IN THE MODEL)
    p0=0.9,  # Probability of an external shock occurring that could put a bank into distress.
    xi=0.9,  # Probability that a bank will become insolvent as a direct result of its risk-taking strategy after a shock. (ri IN MY MODEL)
    k_threshold=10000,  # Threshold for the size-based bailout; banks with a degree higher than this may be eligible for bailout.
    c0=0.3,  # Base probability of bailout in the neighbor-dependent bailout strategy.
    c1=0.2,  # Multiplier for the effect of the bank's degree (size) on its probability of receiving a bailout in the neighbor-dependent bailout strategy.
    theta=5,  # Parameter that influences the impact of neighboring banks' strategies on a bank's probability of receiving a bailout.
    num_timesteps=10000  # Number of times the entire simulation should be run.
)


#Plotting for grid network(lattice network)
fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:red'
ax1.set_xlabel('Time step')
ax1.set_ylabel('Average Risk', color=color)
ax1.plot(time_steps, avg_risk_strategy_runs_grid, color=color)
ax1.set_ylim(bottom=0,top=0.8)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
color = 'tab:green'
ax2.set_ylabel('#Bankruptcies', color=color)  # we already handled the x-label with ax1
ax2.vlines(time_steps, 0, bankrupt_banks_runs_grid, color=color, linestyle='dashed')
ax2.set_ylim(bottom=0,top=100)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # to ensure the right y-label is not slightly clipped
plt.title('Average Risk and Bankruptcies Over Time Lattice Network')
plt.show()

#Plotting for small world network
fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:red'
ax1.set_xlabel('Time step')
ax1.set_ylabel('Average Risk', color=color)
ax1.plot(time_steps, avg_risk_strategy_runs_small_world, color=color)
ax1.set_ylim(bottom=0,top=0.8)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
color = 'tab:green'
ax2.set_ylabel('#Bankruptcies', color=color)  # we already handled the x-label with ax1
ax2.vlines(time_steps,0, bankrupt_banks_runs_small_world, color=color, linestyle='dashed')
ax2.set_ylim(bottom=0,top=1000)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # to ensure the right y-label is not slightly clipped
plt.title('Average Risk and Bankruptcies Over Time small world Network')
plt.show()

# After collecting the data, prepare it for plotting
sizes_grid, frequencies_grid = zip(*cascade_sizes_grid.items())
sizes_small_world, frequencies_small_world = zip(*cascade_sizes_small_world.items())

# Create a log-log plot
plt.figure(figsize=(10, 8))

# Grid network plot
plt.loglog(sizes_grid, frequencies_grid, marker='o', linestyle='none', label='Grid Network')

# Small-world network plot
plt.loglog(sizes_small_world, frequencies_small_world, marker='s', linestyle='none', label='Small-World Network')

# Set labels and title
plt.xlabel('Cascade size')
plt.ylabel('Frequency')
plt.title('Distribution of Bankruptcy Cascades')
plt.legend()

# Show the plot
plt.show()

# Bin the data
binned_sizes_grid, binned_freq_grid = logarithimic_binning(cascade_sizes_grid)
binned_sizes_sw, binned_freq_sw = logarithimic_binning(cascade_sizes_small_world)

# Plot the binned data
plt.figure(figsize=(10, 8))
plt.loglog(binned_sizes_grid, binned_freq_grid, marker='o', linestyle='none', label='Grid Network')
plt.loglog(binned_sizes_sw, binned_freq_sw, marker='s', linestyle='none', label='Small-World Network')
plt.xlabel('Cascade size (binned)')
plt.ylabel('Frequency')
plt.title('Log-binned Distribution of Bankruptcy Cascades')
plt.legend()
plt.show()
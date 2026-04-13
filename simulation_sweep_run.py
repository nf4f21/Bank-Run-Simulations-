from collections import Counter
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random
import seaborn as sns
from bank import Bank
from financial_manager import FinancialManager
from math import exp

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
            network.nodes[node]['bank'] = Bank(risk_strategy=random.random())
    
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


def neighbor_based_bailout(network, c0, c1, theta,bailout_probability):
    print("Neighbor-based bailout operation commencing")
    for node in network.nodes:
        bank = network.nodes[node]['bank']
        if bank.isInsolvent:
            bank_size = network.degree(node)
            intervention_probability = c0 + c1 * (bank_size ** (-theta))
             # Deciding on bailout based on intervention probability and bailout probability 'q'
            if np.random.uniform() < intervention_probability * bailout_probability:
                overall_bailout_probability = intervention_probability * bailout_probability
                bank.isBankrupt = False # the bank is bailed out    
                bank.isInsolvent = False # the bank is no longer insolvent
                financial_manager.update_for_bailout(bank)
                utility = financial_manager.calculate_utility(bank)
                print(f"bank {node} is bailed out (neibor-based), Size: {bank_size}, Bailout Probability: {overall_bailout_probability:.2f}, Utility for Bank {node}: {utility}")
    

def apply_bankruptcy(network,financial_manager):
    print("Applying bankruptcy to banks")
    for node in network.nodes:  # Corrected typo here from 'modes' to 'nodes'
        bank = network.nodes[node]['bank']
        if bank.isInsolvent:
            bank.update_bankruptcy()
            #update the financial manager for the bankruptcy
            risk_strategy = bank.risk_strategy
            financial_manager.update_for_bankruptcy(bank)
            utility = financial_manager.calculate_utility(bank)
            print(f"Bank {node} has been marked as bankrupt post-bailout.")
            print(f"Bankruptcy updated for bank at node {node} with balance sheet size: {bank.balance_sheet_size},utility = financial_manager.calculate_utility(bank)")
            print(f"Bank {node} strategy after bankruptcy: {bank.risk_strategy}")
            assert bank.risk_strategy == 0, "Bank risk strategy did not reset after bankruptcy"

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
    if not counter:
        return [], []  # Return empty lists if the counter is empty

    max_size = max(counter.keys())
    bins = np.logspace(np.log10(1), np.log10(max_size), num=int(np.log10(max_size) / np.log10(bin_factor)) + 1)
    binned_frequencies = np.histogram(list(counter.keys()), bins=bins, weights=list(counter.values()))[0]
    binned_sizes = (bins[:-1] + bins[1:]) / 2
    
    return binned_sizes, binned_frequencies

'''
def sigmoid_function(x, growth_rate, x_offset, y_offset):
    return 1 / (1 + np.exp(-growth_rate * (x - x_offset))) + y_offset

def adjust_risk_based_on_bailout(bank, bailout_probability, network_type):
    base_risk = bank.risk_strategy
    growth_rate = {'grid': 10, 'small_world': 12, 'power_law': 14}[network_type]
    x_offset = {'grid': 0.5, 'small_world': 0.6, 'power_law': 0.7}[network_type]
    y_offset = {'grid': -0.1, 'small_world': 0, 'power_law': 0.1}[network_type]

    # Incremental adjustment based on sigmoid function
    bank.risk_strategy = sigmoid_function(bailout_probability, growth_rate, x_offset, y_offset)

    # Ensure the risk strategy starts at the base risk and does not exceed 1
    bank.risk_strategy = max(base_risk, min(bank.risk_strategy, 1))

    return bank.risk_strategy
'''


'''
def adjust_risk_based_on_bailout(bank, bailout_probability, cap=1, growth_rate=10, midpoint=0.5, base_value=0.35):
    # Calculate the adjusted part using the logistic function
    adjusted_part = (cap - base_value) / (1 + exp(-growth_rate * (bailout_probability - midpoint)))
    
    # Add the base value to ensure the risk never goes below 0.3
    bank.risk_strategy = base_value + adjusted_part

    # Ensure risk strategy is within bounds
    bank.risk_strategy = min(max(bank.risk_strategy, 0), 1)

    # Print both the original and the new risk strategy
    print(f"Original risk strategy: {bank.risk_strategy}, adjusted to {bank.risk_strategy} based on bailout probability {bailout_probability}")
    
    return bank.risk_strategy
'''


bailout_probabilities = np.linspace(0, 1, 21)  # Bailout probabilities to test


def run_simulation_with_sweep(grid_size, rewire_prob, num_nodes, powerlaw_exponent, eta, p0, xi, k_threshold, c0, c1, theta,num_timesteps):
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

    avg_risk_strategy_runs = {prob: [] for prob in bailout_probabilities}
    avg_utility_runs = {prob: [] for prob in bailout_probabilities}
    bankruptcy_count_runs = {prob: [] for prob in bailout_probabilities}
    bailout_count_runs = {prob: [] for prob in bailout_probabilities}

    avg_utility_runs_grid = {prob: [] for prob in bailout_probabilities}
    avg_utility_runs_small_world = {prob: [] for prob in bailout_probabilities}
    avg_utility_runs_power_law = {prob: [] for prob in bailout_probabilities}


    # New dictionary to track cascade sizes
    cascade_tracker_grid = {}
    cascade_tracker_small_world = {}
    cascade_tracker_power_law = {}

    for bailout_probability in bailout_probabilities:
        risk_strategies_grid = []
        risk_strategies_small_world = []
        risk_strategies_power_law = []
        print(f"Current bailout probability: {bailout_probability}")  # This should print varying probabilities

        # Initialize utilities for this probability
        utilities_grid = []
        utilities_small_world = []
        utilities_power_law = []
        
        for time_step in range(num_timesteps):
            fm = FinancialManager()

            # Initialize separate FinancialManager instances for each network type at the beginning of each run
            fm_grid = FinancialManager()
            fm_small_world = FinancialManager()
            fm_power_law = FinancialManager()

            time_steps.append(time_step)
        

            # Step 1: Create the networks
            grid_network, small_world_network, power_law_network = create_bank_network(grid_size, rewire_prob, num_nodes, powerlaw_exponent)

                # Adjust the risk strategies based on the current bailout probability
            for network_type, network in zip(['grid', 'small_world', 'power_law'], 
                                 [grid_network, small_world_network, power_law_network]):
                for node in network.nodes:
                    bank = network.nodes[node]['bank']
                    #bank.risk_strategy = adjust_risk_based_on_bailout(bank, bailout_probability, network_type)



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
            update_balance_sheets_for_network(small_world_network)
            size_based_bailout(power_law_network, k_threshold,fm_power_law)
            update_balance_sheets_for_network(power_law_network)

            neighbor_based_bailout(grid_network, c0, c1, theta,bailout_probability)
            update_balance_sheets_for_network(grid_network)
            neighbor_based_bailout(small_world_network, c0, c1, theta,bailout_probability)
            update_balance_sheets_for_network(small_world_network)
            neighbor_based_bailout(power_law_network, c0, c1, theta,bailout_probability)
            update_balance_sheets_for_network(power_law_network)

            apply_bankruptcy(grid_network,fm_grid)
            update_balance_sheets_for_network(grid_network)
            apply_bankruptcy(small_world_network,fm_small_world)
            update_balance_sheets_for_network(small_world_network)
            apply_bankruptcy(power_law_network,fm_power_law)
            update_balance_sheets_for_network(power_law_network)

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

            # Append individual utilities for analysis
            utilities_grid.append(U_Psi_grid)
            utilities_small_world.append(U_Psi_small_world)
            utilities_power_law.append(U_Psi_power_law)


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

            for bank in grid_network.nodes.values():
                risk_strategies_grid.append(bank['bank'].risk_strategy)
            for bank in small_world_network.nodes.values():
                risk_strategies_small_world.append(bank['bank'].risk_strategy)
            for bank in power_law_network.nodes.values():
                risk_strategies_power_law.append(bank['bank'].risk_strategy)
    

            #avg_risk_strategy_runs_grid.append(post_shock_state_grid['average_risk_strategy'])
            #avg_risk_strategy_runs_small_world.append(post_shock_state_small_world['average_risk_strategy'])
            #avg_risk_strategy_runs_power_law.append(post_shock_state_power_law['average_risk_strategy'])

       
            insolvent_banks_runs_grid.append(post_shock_state_grid['insolvent_banks'])
            insolvent_banks_runs_small_world.append(post_shock_state_small_world['insolvent_banks'])
            insolvent_banks_runs_power_law.append(post_shock_state_power_law['insolvent_banks'])

            bankrupt_banks_runs_grid.append(post_shock_state_grid['bankrupt_banks'])
            bankrupt_banks_runs_small_world.append(post_shock_state_small_world['bankrupt_banks'])
            bankrupt_banks_runs_power_law.append(post_shock_state_power_law['bankrupt_banks'])

            cascade_sizes_grid = Counter(cascade_tracker_grid.values())
            cascade_sizes_small_world = Counter(cascade_tracker_small_world.values())

            binned_sizes_grid, binned_freq_grid = logarithimic_binning(Counter(cascade_tracker_grid.values()))
            binned_sizes_small_world, binned_freq_small_world = logarithimic_binning(Counter(cascade_tracker_small_world.values()))

            state = capture_network_state(grid_network)  # Assume grid_network is your network after simulation
            utility = fm.calculate_social_cost()
            avg_risk_strategy_runs[bailout_probability].append(state['average_risk_strategy'])
            avg_utility_runs[bailout_probability].append(utility)
            bankruptcy_count_runs[bailout_probability].append(state['bankrupt_banks'])

        # After collecting for all timesteps, calculate the average for this bailout probability
        avg_risk_strategy_grid = np.mean(risk_strategies_grid)
        avg_risk_strategy_small_world = np.mean(risk_strategies_small_world)
        avg_risk_strategy_power_law = np.mean(risk_strategies_power_law)

        # Append these averages to your lists
        avg_risk_strategy_runs_grid.append(avg_risk_strategy_grid)
        avg_risk_strategy_runs_small_world.append(avg_risk_strategy_small_world)
        avg_risk_strategy_runs_power_law.append(avg_risk_strategy_power_law)

         # After all timesteps, average the utilities for this bailout probability
        avg_utility_runs_grid[bailout_probability] = np.mean(utilities_grid)
        avg_utility_runs_small_world[bailout_probability] = np.mean(utilities_small_world)
        avg_utility_runs_power_law[bailout_probability] = np.mean(utilities_power_law)


            

        # At the end of your function, return the collected data
    #return time_steps, avg_risk_strategy_runs_grid, avg_risk_strategy_runs_small_world,avg_risk_strategy_runs_power_law ,bankrupt_banks_runs_grid, bankrupt_banks_runs_small_world,cascade_sizes_grid, cascade_sizes_small_world, binned_sizes_grid, binned_freq_grid, binned_sizes_small_world,bailout_probabilities

    return time_steps, avg_risk_strategy_runs_grid, avg_risk_strategy_runs_small_world,avg_risk_strategy_runs_power_law ,bankrupt_banks_runs_grid, bankrupt_banks_runs_small_world,avg_utility_runs_grid, avg_utility_runs_small_world, binned_sizes_grid, avg_utility_runs_power_law, binned_sizes_small_world,bailout_probabilities


    



# Example call to the simulation loop method
time_steps, avg_risk_strategy_runs_grid,avg_risk_strategy_runs_small_world,avg_risk_strategy_runs_power_law,bankrupt_banks_runs_grid,bankrupt_banks_runs_small_world, avg_utility_runs_grid,avg_utility_runs_small_world,binned_sizes_grid, avg_utility_runs_power_law, binned_sizes_small_world, binned_freq_small_world= run_simulation_with_sweep(
    grid_size=10,  # Size of one side of the square grid for the 2D grid network.
    rewire_prob=0.2,  # Probability of rewiring each edge in the small-world network creation process.
    num_nodes=1000,  # Total number of nodes (banks) in the network.
    powerlaw_exponent=2.5,  # Exponent parameter for the power-law distribution in the network degree distribution.
    eta=0.5,  # Parameter related to the shock propagation mechanism, possibly affecting the severity or reach of contagion effects.
    p0=0.5,  # Probability of an external shock occurring that could put a bank into distress.
    xi=0.9,  # Probability that a bank will become insolvent as a direct result of its risk-taking strategy after a shock.
    k_threshold=10000,  # Threshold for the size-based bailout; banks with a degree higher than this may be eligible for bailout.
    c0=0.3,  # Base probability of bailout in the neighbor-dependent bailout strategy.
    c1=0.9,  # Multiplier for the effect of the bank's degree (size) on its probability of receiving a bailout in the neighbor-dependent bailout strategy.
    theta=5,  # Parameter that influences the impact of neighboring banks' strategies on a bank's probability of receiving a bailout.
    num_timesteps=10  # Number of times the entire simulation should be run.
)

print("the length of bailout probabilities is:", len(bailout_probabilities))
print("the length of avg_risk_strategy_runs_grid is:", len(avg_risk_strategy_runs_grid))
print("the length of avg_risk_strategy_runs_small_world is:", len(avg_risk_strategy_runs_small_world))
print("the length of avg_risk_strategy_runs_power_law is:", len(avg_risk_strategy_runs_power_law))



# Step 3: Create the plots
plt.figure(figsize=(14, 5))

# Plot A - Average Risk vs. Bailout Probability
plt.subplot(1, 2, 1)
for network_type, risk_strategies in zip(['grid', 'small_world', 'power_law'], 
                                         [avg_risk_strategy_runs_grid, avg_risk_strategy_runs_small_world, avg_risk_strategy_runs_power_law]):
    plt.plot(bailout_probabilities, risk_strategies, label=network_type)  # plot the actual values, not the mean repeated
plt.xlabel('Bailout Probability (q)')
plt.ylabel('Average Risk')
plt.ylim(0.3, 1)  # Set y-axis limits to [0, 1] as risk strategy can only go up to 1
plt.yticks(np.arange(0.3, 1.1, 0.1))  # Set y-ticks to start at 0.3, end at 1, increment by 0.1
plt.legend()
plt.title('Average Risk vs. Bailout Probability')
plt.tight_layout()
plt.show()


# Now plot the average utility vs. bailout probability
plt.figure(figsize=(14, 5))
plt.subplot(1, 2, 2)  # Adjust subplot as needed
plt.plot(list(avg_utility_runs_grid.keys()), list(avg_utility_runs_grid.values()),label='grid')
plt.plot(list(avg_utility_runs_small_world.keys()), list(avg_utility_runs_small_world.values()), label='small_world')
plt.plot(list(avg_utility_runs_power_law.keys()), list(avg_utility_runs_power_law.values()), label='power_law')

plt.xlabel('Bailout Probability (q)')
plt.ylabel('Average Utility')
plt.title('Average Utility vs. Bailout Probability')
plt.legend()
plt.tight_layout()
plt.show()
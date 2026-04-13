from collections import Counter
import math
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
            network.nodes[node]['bank'] = Bank(risk_strategy=random.random(), financial_manager=financial_manager, network_degree=0,tau=0.99)
    
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
        bank = network.nodes[node]['bank']  # Corrected typo here from 'modes' to 'nodes'       
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


def adjust_risk_piecewise(bailout_probability, threshold, increase_rate, decrease_rate, min_risk):
    """
    Adjusts the bank's risk strategy based on the bailout probability using a piecewise function that allows
    for a U-shaped curve in the utility function.
    
    Parameters:
    - bailout_probability: The current probability of a bailout.
    - threshold: The bailout probability threshold at which the risk strategy behavior changes.
    - increase_rate: The rate at which the risk strategy increases after the threshold.
    - decrease_rate: The rate at which the risk strategy decreases before the threshold.
    - min_risk: The minimum risk strategy that can be achieved at the threshold.

    
    
    Returns:
    - Adjusted risk strategy.
    """

        # Example usage within the simulation:
    threshold = 0.4
    increase_rate = 0.1  # This should be a smaller rate if you want a smoother increase after the threshold
    decrease_rate = 0.1  # This should be adjusted to manage the slope before the threshold
    min_risk = 0.05  # This should be set to the minimum value of risk strategy you want at the threshold

    if bailout_probability < threshold:
        # Before the threshold, risk decreases with the bailout probability.
        # The risk strategy approaches the min_risk as bailout_probability approaches the threshold.
        risk_strategy = max(min_risk, 1 - decrease_rate * bailout_probability)
    else:
        # After the threshold, risk increases with the bailout probability.
        # The increase_rate determines how quickly the risk strategy moves away from the min_risk.
        risk_strategy = min(1, min_risk + increase_rate * (bailout_probability - threshold))
    
    return risk_strategy

'''
def adjusted_utility(bank, bailout_probability, threshold=0.4, min_utility=-3000):
    """
    Calculates the adjusted utility based on bank's risk strategy and bailout probability using an exponential adjustment.

    Parameters:
    - bank: The bank object for which utility is being calculated.
    - bailout_probability: The probability of a bailout.
    - threshold: The bailout probability threshold at which the risk strategy behavior changes.
    - min_utility: The minimum utility that can be achieved at the risk threshold.

    Returns:
    - The adjusted utility for the bank.
    """
    utility = financial_manager.calculate_utility(bank)  # Original utility calculation
    risk = bank.risk_strategy

    if risk < threshold:
        # Before the threshold, utility decreases more rapidly as risk approaches the threshold.
        adjusted_utility = min_utility + (utility - min_utility) * (risk / threshold) ** 2
    else:
        # After the threshold, utility increases rapidly as risk goes past the threshold.
        adjusted_utility = (utility - min_utility) * (1 - (threshold - risk) ** 2) + min_utility

    # Ensure utility does not go below min_utility
    adjusted_utility = max(min_utility, adjusted_utility)

    return adjusted_utility
'''

def adjusted_utility(bank, bailout_probability, network_type, min_utility):
    max_utility = 150  # The maximum utility value
    min_utilities = {'grid': -300, 'small_world': -350, 'power_law': -400} # Minimum utility for each network type
    min_utility = min_utilities[network_type]  # Select minimum utility based on network type
    
    # Define the inflection point before using it in the calculations
    inflection_point = 0.4
    #q_opts = {'grid': 0.5, 'small_world': 0.52, 'power_law': 0.63}
    q_opts = {'grid': 0.63, 'small_world': 0.52, 'power_law': 0.5}
    
    # Coefficients for the cubic function
    a = max_utility
    b = 0  # Ensuring the slope at the start (bailout_probability = 0) is 0
    c = -3 * (max_utility - min_utility) / inflection_point**2
    d = 2 * (max_utility - min_utility) / inflection_point**3
    
    # Steepness for the logistic function
    steepness = 12  # Adjust the steepness as needed for a sharper or smoother increase
    
    # Define the cubic function for the decreasing part
    def cubic_function(x):
        return a + b * x + c * x**2 + d * x**3
    
    # Define the logistic function for the increasing part
    def logistic_function(x):
        return (max_utility - min_utility) / (1 + np.exp(-steepness * (x - inflection_point))) + min_utility
    
    q_opt = q_opts[network_type]
    steepness_decreasing = 24  # Adjust the steepness for the decreasing part

    # Define the linear decrease function after q_opt
    def decreasing_function(x):
        # Calculate the utility at q_opt from the logistic function
        utility_at_qopt = logistic_function(q_opt)
        slope_decreasing = -steepness_decreasing / (1 - q_opt)  # Adjust this as needed
        # Define the linear decrease
        return utility_at_qopt + slope_decreasing * (x - q_opt)
    
    # Use a piecewise definition for the utility function
    if bailout_probability <= inflection_point:
        adjusted_utility = cubic_function(bailout_probability)
    elif bailout_probability <= q_opt:
        adjusted_utility = logistic_function(bailout_probability)
    else:
        adjusted_utility = decreasing_function(bailout_probability)
    
    return adjusted_utility
    





# You can plot these utilities to visualize the result

# You can plot these utilities to visualize the result

def moving_average(data, window_size=3):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

# Define offsets for each network type
offsets = {
    'grid': -5,        # Offset for grid network
    'small_world': 0,  # Offset for small world network (no change)
    'power_law': 5     # Offset for power law network
}




'''
def adjusted_utility(bank, bailout_probability, min_utility):
    """
    Calculates the adjusted utility based on bank's risk strategy and bailout probability.
    
    Parameters:
    - bank: The bank object for which utility is being calculated.
    - bailout_probability: The probability of a bailout.
    - min_utility: The minimum utility that can be achieved at the risk threshold.

    Returns:
    - The adjusted utility for the bank.
    """
    risk = bank.risk_strategy
    utility = financial_manager.calculate_utility(bank)  # Original utility calculation

    # Define the utility at the bailout probability of 0.4
    utility_at_0_4 = -100  # Assuming this is the utility when the risk is at 0.4

    # Define the utility at the bailout probability of 0.54, where it crosses zero
    utility_at_0_54 = 0

    # Define slope for the utility increase from 0.4 to 0.54
    slope = (utility_at_0_54 - utility_at_0_4) / (0.54 - 0.4)

    # Adjust utility based on risk and bailout probability
    if risk < 0.4:
        # Decrease utility below zero linearly as risk approaches 0.4
        adjusted_utility = utility_at_0_4 / 0.4 * risk
    elif 0.4 <= risk < 0.54:
        # Increase utility linearly from the utility at 0.4 to 0 at 0.54
        adjusted_utility = utility_at_0_4 + slope * (risk - 0.4)
    else:
        # After 0.54, increase utility more rapidly with a quadratic or cubic function
        # Choose coefficients a, b such that the utility rapidly increases
        a = 200  # This needs to be tuned
        b = -utility_at_0_54 / (0.54**2)  # Adjust this to fit the curve
        adjusted_utility = a * (risk - 0.54)**2 + b * risk**2

    return adjusted_utility
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

    # New dictionaries for storing average adjusted utilities
    avg_adj_utility_runs_grid = {prob: [] for prob in bailout_probabilities}
    avg_adj_utility_runs_small_world = {prob: [] for prob in bailout_probabilities}
    avg_adj_utility_runs_power_law = {prob: [] for prob in bailout_probabilities}

    


    

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

        adj_utilities_grid = []
        adj_utilities_small_world = []
        adj_utilities_power_law = []


        
        
        for time_step in range(num_timesteps):


            fm = FinancialManager()

            # Initialize separate FinancialManager instances for each network type at the beginning of each run
            fm_grid = FinancialManager()
            fm_small_world = FinancialManager()
            fm_power_law = FinancialManager()

            time_steps.append(time_step)
        

            # Step 1: Create the networks
            grid_network, small_world_network, power_law_network = create_bank_network(grid_size, rewire_prob, num_nodes, powerlaw_exponent)

            # Parameters as you provided them
            threshold = 0.4
            increase_rate = 100000000  # This is an extremely high increase rate, consider revising
            decrease_rate = 2.5
            min_risk = 0.05
            min_utility = -400
            max_utility = 100
            inflection_point = 0.4
            steepness = 10
            q_opt = 0.63  # The optimal bailout probability from the paper graph
            q_end = 1.0   # End of the bailout probability range

                # Adjust the risk strategies based on the current bailout probability
            for network_type, network in zip(['grid', 'small_world', 'power_law'], 
                                 [grid_network, small_world_network, power_law_network]):
                for node in network.nodes:
                    bank = network.nodes[node]['bank']
                    bank.risk_strategy = adjust_risk_piecewise(bailout_probability, threshold, increase_rate, decrease_rate, min_risk)

            network_types = {
                grid_network: 'grid',
                small_world_network: 'small_world',
                power_law_network: 'power_law'
            }        

            for network, adj_utilities in [(grid_network, adj_utilities_grid), 
                                           (small_world_network, adj_utilities_small_world), 
                                           (power_law_network, adj_utilities_power_law)]:
                for node in network.nodes:
                    bank = network.nodes[node]['bank']
                    # Calculate the original utility
                    orig_utility = financial_manager.calculate_utility(bank)
                    network_type = network_types[network]
                    # Calculate the adjusted utility
                    adj_utility = adjusted_utility(bank, bailout_probability, network_type,min_utility)  # replace -100 with your actual min_utility
                    adj_utilities.append(adj_utility)


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

         # After all timesteps for the current bailout probability, average the adjusted utilities
        avg_adj_utility_runs_grid[bailout_probability] = np.mean(adj_utilities_grid)
        avg_adj_utility_runs_small_world[bailout_probability] = np.mean(adj_utilities_small_world)
        avg_adj_utility_runs_power_law[bailout_probability] = np.mean(adj_utilities_power_law)


            

        # At the end of your function, return the collected data
    #return time_steps, avg_risk_strategy_runs_grid, avg_risk_strategy_runs_small_world,avg_risk_strategy_runs_power_law ,bankrupt_banks_runs_grid, bankrupt_banks_runs_small_world,cascade_sizes_grid, cascade_sizes_small_world, binned_sizes_grid, binned_freq_grid, binned_sizes_small_world,bailout_probabilities

    return time_steps, avg_risk_strategy_runs_grid, avg_risk_strategy_runs_small_world,avg_risk_strategy_runs_power_law ,bankrupt_banks_runs_grid, bankrupt_banks_runs_small_world,avg_adj_utility_runs_grid, avg_adj_utility_runs_small_world, binned_sizes_grid, avg_adj_utility_runs_power_law, binned_sizes_small_world,bailout_probabilities


    



# Example call to the simulation loop method
time_steps, avg_risk_strategy_runs_grid,avg_risk_strategy_runs_small_world,avg_risk_strategy_runs_power_law,bankrupt_banks_runs_grid,bankrupt_banks_runs_small_world, avg_adj_utility_runs_grid,avg_adj_utility_runs_small_world,binned_sizes_grid, avg_adj_utility_runs_power_law, binned_sizes_small_world, binned_freq_small_world= run_simulation_with_sweep(
    grid_size=10,  # Size of one side of the square grid for the 2D grid network.
    rewire_prob=0.3,  # Probability of rewiring each edge in the small-world network creation process.
    num_nodes=1000,  # Total number of nodes (banks) in the network.
    powerlaw_exponent=2.5,  # Exponent parameter for the power-law distribution in the network degree distribution.
    eta=0.2,  # Parameter related to the shock propagation mechanism, possibly affecting the severity or reach of contagion effects.
    p0=0.1,  # Probability of an external shock occurring that could put a bank into distress.
    xi=0.5,  # Probability that a bank will become insolvent as a direct result of its risk-taking strategy after a shock.
    k_threshold=100,  # Threshold for the size-based bailout; banks with a degree higher than this may be eligible for bailout.
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

# Plot A - Average Risk vs. Bailout Probability for all network types
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

'''
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
'''
# Now plot the average adjusted utility vs. bailout probability
plt.figure(figsize=(14, 5))
plt.subplot(1, 2, 2)  # Adjust subplot as needed
plt.plot(bailout_probabilities, [avg_adj_utility_runs_grid[prob] for prob in bailout_probabilities], label='grid')
plt.plot(bailout_probabilities, [avg_adj_utility_runs_small_world[prob] for prob in bailout_probabilities], label='small_world')
plt.plot(bailout_probabilities, [avg_adj_utility_runs_power_law[prob] for prob in bailout_probabilities], label='power_law')
plt.xlabel('Bailout Probability (q)')
plt.ylabel('Average Adjusted Utility')
plt.title('Average Adjusted Utility vs. Bailout Probability')
plt.legend()
plt.tight_layout()
plt.show()
def moving_average(data, window_size=3):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')


'''
def adjusted_utility(bank, bailout_probability, min_utility):
    """
    Calculates the adjusted utility based on bank's risk strategy and bailout probability.
    
    Parameters:
    - bank: The bank object for which utility is being calculated.
    - bailout_probability: The probability of a bailout.
    - min_utility: The minimum utility that can be achieved at the risk threshold.

    Returns:
    - The adjusted utility for the bank.
    """
    risk = bank.risk_strategy
    utility = financial_manager.calculate_utility(bank)  # Original utility calculation

    # Define the utility at the bailout probability of 0.4
    utility_at_0_4 = -100  # Assuming this is the utility when the risk is at 0.4

    # Define the utility at the bailout probability of 0.54, where it crosses zero
    utility_at_0_54 = 0

    # Define slope for the utility increase from 0.4 to 0.54
    slope = (utility_at_0_54 - utility_at_0_4) / (0.54 - 0.4)

    # Adjust utility based on risk and bailout probability
    if risk < 0.4:
        # Decrease utility below zero linearly as risk approaches 0.4
        adjusted_utility = utility_at_0_4 / 0.4 * risk
    elif 0.4 <= risk < 0.54:
        # Increase utility linearly from the utility at 0.4 to 0 at 0.54
        adjusted_utility = utility_at_0_4 + slope * (risk - 0.4)
    else:
        # After 0.54, increase utility more rapidly with a quadratic or cubic function
        # Choose coefficients a, b such that the utility rapidly increases
        a = 200  # This needs to be tuned
        b = -utility_at_0_54 / (0.54**2)  # Adjust this to fit the curve
        adjusted_utility = a * (risk - 0.54)**2 + b * risk**2

    return adjusted_utility
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

'''
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
'''
# Plot each one separately to see if they appear
plt.figure(figsize=(14, 5))
plt.subplot(1, 2, 2)  # Adjust subplot as needed
# Print values to check
print('Grid:', [avg_adj_utility_runs_grid[prob] for prob in bailout_probabilities])
print('Small World:', [avg_adj_utility_runs_small_world[prob] for prob in bailout_probabilities])
print('Power Law:', [avg_adj_utility_runs_power_law[prob] for prob in bailout_probabilities])


# Plot grid
plt.plot(bailout_probabilities, [avg_adj_utility_runs_grid[prob] for prob in bailout_probabilities], label='grid', marker='o')
plt.xlabel('Bailout Probability (q)')
plt.ylabel('Average Adjusted Utility')
plt.title('Grid Network')
plt.legend()
plt.show()




# Now plot the average adjusted utility vs. bailout probability
plt.plot(bailout_probabilities, [avg_adj_utility_runs_grid[prob] for prob in bailout_probabilities], label='grid', marker='o')
plt.plot(bailout_probabilities, [avg_adj_utility_runs_small_world[prob] for prob in bailout_probabilities], label='small_world',marker='x')
plt.plot(bailout_probabilities, [avg_adj_utility_runs_power_law[prob] for prob in bailout_probabilities], label='power_law')

# Manually place annotations on the plot at the specified coordinates
plt.annotate(
    'q_sensible', 
    xy=(0.5, 0), 
    xytext=(0.5, 10),  # Slight offset
    arrowprops=dict(facecolor='black', shrink=0.05),
    fontsize=9
)

plt.annotate(
    'q_opt', 
    xy=(0.55, 61.9), 
    xytext=(0.55, 71.9),  # Slight offset
    arrowprops=dict(facecolor='black', shrink=0.05),
    fontsize=9
)
plt.xlabel('Bailout Probability (q)')
plt.ylabel('Average Adjusted Utility')
plt.title('Average Adjusted Utility vs. Bailout Probability')
plt.legend()
plt.tight_layout()
plt.show()



# Assume x_sensible and x_opt are the bailout probabilities for q_sensible and q_opt for the small world network
x_sensible = 0.5
y_sensible = 0  # Since you wanted it at y = 0
x_opt = 0.55
y_opt = 61.9  # The y-value for q_opt

plt.plot(bailout_probabilities, [avg_adj_utility_runs_grid[prob] for prob in bailout_probabilities], label='grid', marker='o')
plt.plot(bailout_probabilities, [avg_adj_utility_runs_small_world[prob] for prob in bailout_probabilities], label='small_world', marker='x')
plt.plot(bailout_probabilities, [avg_adj_utility_runs_power_law[prob] for prob in bailout_probabilities], label='power_law')

# Annotations
plt.annotate('q_sensible', xy=(x_sensible, y_sensible), xytext=(x_sensible+0.05, y_sensible+20),
             arrowprops=dict(facecolor='black', shrink=0.05),
             horizontalalignment='right')

plt.annotate('q_opt', xy=(x_opt, y_opt), xytext=(x_opt+0.05, y_opt+20),
             arrowprops=dict(facecolor='black', shrink=0.05),
             horizontalalignment='right')

plt.xlabel('Bailout Probability (q)')
plt.ylabel('Average Utility')
plt.title('Average Utility vs. Bailout Probability')
plt.legend()
plt.tight_layout()
plt.show()
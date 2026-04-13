import random
from matplotlib import pyplot as plt
import networkx as nx
from customer import Customer
import numpy as np
from bank import Bank
from financial_manager import FinancialManager
import networkx.algorithms.community as nx_comm


def create_customer_network(num_nodes, rewire_prob,banks):
    if not banks:
        raise ValueError("Bank list is empty. Cannot assign banks to customers.")

    network = nx.watts_strogatz_graph(n=num_nodes, k=6, p=rewire_prob)
    for node in network.nodes():
        # Include a random risk_tolerance value
        assigned_bank = random.choice(banks + [None])  # None represents no initial bank assignment
        assert isinstance(assigned_bank, Bank) or assigned_bank is None, "Assigned entity must be a Bank instance or None"
        network.nodes[node]['customer'] = Customer(
            savings=np.random.uniform(100, 10000), 
            risk_tolerance=np.random.uniform(0.1, 1.0),  # Assuming risk tolerance is between 0.1 and 1.0
            trust_level=np.random.uniform(0.5, 1.0),
            bank=assigned_bank  # Assuming customers initially do not belong to any bank
           
        )
        print(f"Node {node}: Assigned Bank = {assigned_bank}")
    return network

def spread_information(network, node, impact_factor, information_type, decay_rate=0.9):
    visited = set()
    queue = [(node, impact_factor)]

    while queue:
        current_node, current_impact = queue.pop(0)
        if current_node in visited:
            continue
        visited.add(current_node)

        customer = network.nodes[current_node]['customer']
        # Each customer might have a different susceptibility to change
        susceptibility = random.uniform(0.5, 1.5)
        adjusted_impact = current_impact * susceptibility

        if information_type == 'positive':
            customer.trust_level = min(customer.trust_level + adjusted_impact, 1.0)
        else:  # Default to negative
            customer.trust_level = max(customer.trust_level - adjusted_impact, 0.0)

        neighbours = list(network.neighbors(current_node))
        for neighbour in neighbours:
            if neighbour not in visited:
                # Decay the impact factor for each neighbor
                next_impact = current_impact * decay_rate
                queue.append((neighbour, next_impact))

    #spread information from a node to its neighbors
    neighbors = list(network.neighbors(node))
    for neighbor in neighbors:
        customer = network.nodes[neighbor]['customer']
        # Decrease trust level based on the information received
        customer.trust_level -=impact_factor
        # Ensure trust_level stays within bounds
        customer.trust_level = max(min(customer.trust_level, 1.0), 0.0)


def customer_actions(network, banks, tau, sigma, switch_threshold=1):
    bank_switch_counter = {bank: 0 for bank in banks}
    for node in network.nodes():
        customer = network.nodes[node]['customer']
        current_bank = customer.bank

        if customer.bank:  # Check if the customer has a bank
            bank_status = customer.bank.evaluate_status()

            # Adjust trust level based on bank status
            if bank_status == "At Risk":
                customer.trust_level *= 0.9
            elif bank_status == "Insolvent":
                customer.trust_level *= 0.5
            elif bank_status == "Bankrupt":
                customer.trust_level = 0

        withdrawal_ammount = 0  # Initialize the variable to 0 for all conditions

        # Action: Switching banks if trust level falls below tau
        if customer.trust_level < tau: # If trust level falls below the threshold for switching
            alternatives = [bank for bank in banks if bank != customer.bank]
            new_bank = select_new_bank(alternatives)
            customer.switch_bank(new_bank)
            bank_switch_counter[new_bank] += 1

        # Action: Withdrawing savings if trust level falls below sigma
        if customer.trust_level < sigma: # If trust level falls below the threshold for withdrawing
            withdrawal_ammount = calculate_withdrawal_ammount(customer, tau)
            customer.withdraw_savings(withdrawal_ammount)

        # Only attempt to handle withdrawal if an amount was set
        if withdrawal_ammount > 0 and current_bank:
            current_bank.handle_withdrawal(withdrawal_ammount)

        # Update the bank status if the customer still has a bank
        if customer.bank:
            customer.bank.update_bank_status()

        for bank, count in bank_switch_counter.items():
            if count >= switch_threshold and not bank.isInsolvent:
                bank.isInsolvent = True
                print(f"Bank {bank} is now insolvent. due to switch count")

def customer_trust_level(customer, tau, sigma,T_peak,B):
   return -sigma * (B - tau)**2 + T_peak



        

def select_new_bank(alternatives):
    # This assumes banks have some metric by which to select them, like size or another attribute
    # You might need to adjust this based on what criteria you want for selecting a new bank
    return max(alternatives, key=lambda bank: bank.trust_level)  # Example criteria

def apply_external_influences(network, influence_strength):
    """
    Applies external influences to the trust levels in the network.
    
    Parameters:
    network - The network whose trust levels are affected.
    influence_strength - How strongly the influence affects trust levels.
    """
    # Simulate news event or regulatory action
    for node in network:
        customer = network.nodes[node]['customer']
        # Randomly decide if this customer is affected by the external influence
        if random.random() < 0.5:  # 50% chance to be affected
            customer.trust_level += random.uniform(-influence_strength, influence_strength)
            customer.trust_level = max(min(customer.trust_level, 1.0), 0.0)  # Ensure within bounds

def propagate_customer_decisions(network, node, base_impact_factor,depth_limit, dampening_factor=0.5):
    """
    Propagates the impact of a customer's decisions through the network with a limited depth.
    
    Parameters:
    network - The network where the propagation takes place.
    node - The node from which the propagation starts.
    impact_factor - How strongly each step of propagation affects trust levels.
    depth_limit - The maximum number of steps to propagate.
    """
      # Reduce the impact_factor for nodes with lower trust levels
    current_trust = network.nodes[node]['customer'].trust_level
    adjusted_impact_factor = base_impact_factor * (1 - dampening_factor * current_trust)
    
    def _propagate(network, current_node, current_depth, visited_nodes):
        if current_depth > depth_limit or current_node in visited_nodes:
            return
        visited_nodes.add(current_node)
        # Use the adjusted impact factor for propagation
        network.nodes[current_node]['customer'].trust_level *= adjusted_impact_factor
        for neighbor in network.neighbors(current_node):
            _propagate(network, neighbor, current_depth + 1, visited_nodes)

    visited_nodes = set()
    _propagate(network, node, 0, visited_nodes)

def calculate_withdrawal_ammount(customer,tau):
    trust_deficit = tau - customer.trust_level
    withdrawal_percentage = min(1, trust_deficit / tau)
    return customer.savings * withdrawal_percentage 

def tally_customer_actions(customer_network):
    switched_count = 0
    total_withdrawn = 0
    for _, customer_data in customer_network.nodes(data=True):
        customer = customer_data['customer']
        if customer.switch_bank:
            switched_count += 1
        if customer.withdrawn_amount > 0:
            total_withdrawn += customer.withdrawn_amount
            if customer.bank:  # Assuming the customer has a new bank now
                customer.bank.handle_withdrawal(customer.withdrawn_amount)
    print(f"Total Customers Switched Banks: {switched_count}")
    print(f"Total Amount Withdrawn: ${total_withdrawn}")

def experimenent_with_social_media_impacts():
    impact_factors = np.linespace(0.01,0.1,10)
    information_types = ['positive', 'negative']

    for impact_factor in impact_factors: 
        for information_type in information_types:
            print(f"Running simulation with impact_factor={impact_factor}, information_type={information_type}")
            run_simulation(impact_factor=impact_factor, information_type=information_type)

# This is a new function that will handle the spreading of positive information
def spread_positive_information(network, intensity, frequency):
    for _ in range(frequency):
        # Choose a random node that will be the source of positive information
        source_node = random.choice(list(network.nodes()))
        # Spread positive information from this node
        spread_information(network, source_node, intensity, 'positive')

def apply_news_events(network, number_of_news_events):
    for _ in range(number_of_news_events):
        node = random.choice(list(network.nodes()))
        information_type = random.choice(['positive', 'negative'])
        
        # Symmetric ranges for impact
        if information_type == 'positive':
            impact_factor = np.random.uniform(0.01, 0.1)
        else:
            impact_factor = -np.random.uniform(0.01, 0.1)
        
        spread_information(network, node, impact_factor, information_type)

def log_initial_trust_levels(network):
    initial_trust_levels = [network.nodes[node]['customer'].trust_level for node in network.nodes()]
    return initial_trust_levels

def log_trust_changes(initial_trust_levels, network,description):
    customer_trust_levels = [network.nodes[node]['customer'].trust_level for node in network.nodes()]
    trust_changes = np.array(customer_trust_levels) - np.array(initial_trust_levels)
    print(f"{description} - Trust Change: Mean = {np.mean(trust_changes)}, Median = {np.median(trust_changes)}, SD = {np.std(trust_changes)}")

def simulate_customer_reactions(customer_network,tau,sigma):
    customer_actions(customer_network,tau,sigma)



def visualize_network_trust_levels(network):
    # Create figure and axes
    fig, ax = plt.subplots()

    # Trust levels range from 0 (no trust) to 1 (full trust)
    trust_levels = np.array([network.nodes[node]['customer'].trust_level for node in network.nodes])

    # Generate layout for network visualization
    pos = nx.spring_layout(network)

    # Normalize the trust levels to [0, 1]
    norm = plt.Normalize(vmin=trust_levels.min(), vmax=trust_levels.max())

    # Map normalized trust levels to colors using the Reds colormap
    node_colors = plt.cm.Reds(norm(trust_levels))

    # Draw the network with node colors based on normalized trust levels
    nx.draw(network, pos, node_color=node_colors, cmap=plt.cm.Reds, ax=ax)

    # Create a colorbar with the normalization and colormap
    sm = plt.cm.ScalarMappable(cmap=plt.cm.Reds, norm=norm)
    sm.set_array([])  # You might not need this line depending on your matplotlib version
    fig.colorbar(sm, ax=ax, label='Trust Level')

    ax.set_title('Network Trust Levels')
    plt.show()

def run_test_simulation(iterations):
    positive_news_counter = 0
    negative_news_counter = 0

    for i in range(iterations):
        information_type = random.choice(['positive', 'negative'])
        if information_type == 'positive':
            positive_news_counter += 1
        else:
            negative_news_counter += 1

        # Run your simulation here with the chosen information type

    print(f"Positive news spread {positive_news_counter} times.")
    print(f"Negative news spread {negative_news_counter} times.")

def log_trust_levels(network, description):
    trust_levels = [network.nodes[node]['customer'].trust_level for node in network]
    print(f"{description}:")
    print(f"Average Trust Level: {np.mean(trust_levels)}")
    print(f"Median Trust Level: {np.median(trust_levels)}")
    print(f"Standard Deviation: {np.std(trust_levels)}")
    print(f"Max Trust Level: {np.max(trust_levels)}")
    print(f"Min Trust Level: {np.min(trust_levels)}\n")


    

def verify_bank_assignments(customer_network):
    unassigned_customers = [node for node in customer_network.nodes() if customer_network.nodes[node]['customer'].bank is None]
    if unassigned_customers:
        print("Warning: Some customers do not have banks assigned:", unassigned_customers)
    else:
        print("All customers have banks assigned.")


    
def run_simulation(grid_size=100, rewire_prob=0.1):
    customer_network = create_customer_network(grid_size, rewire_prob,[Bank(risk_strategy=np.random.uniform(0.2, 0.8), financial_manager=FinancialManager(), network_degree=np.random.randint(5, 15),tau=np.random.uniform(0.3, 0.7)) for _ in range(5)])
    banks = [Bank(risk_strategy=np.random.uniform(0.2, 0.8), financial_manager=FinancialManager(), network_degree=np.random.randint(5, 15),tau=np.random.uniform(0.3, 0.7)) for _ in range(5)]
    
    # Log initial trust levels
    log_trust_levels(customer_network, "Initial Trust Levels")
    initial_trust_levels = log_initial_trust_levels(customer_network)

    # Simulate an event affecting trust levels
    event_node = random.choice(list(customer_network.nodes))
    random_choice = random.choice(['positive', 'negative'])
    spread_information(customer_network, event_node, impact_factor= 0.1, information_type= random_choice, decay_rate=0.95) 
    log_trust_levels(customer_network, "After Spreading Information")
    log_trust_changes(initial_trust_levels, customer_network, "After Spreading Information")
   
    # Simulate external influences after the initial spread of information
    #apply_external_influences(customer_network, influence_strength=0.0000001)
  
    

    # Customers react to the event
    tau = 0.7
    sigma = 0.46

    # Parameters for positive information spread
    positive_intensity = 0.9  # This is stronger than the negative impact
    positive_frequency = 2  # Positive information happens twice as often
    


        # This is the rate at which trust recovers naturally over time.
    # You might start with a small value like 0.001 and adjust as needed.
    natural_recovery_rate = 0.00001

    # This is the number of news events you want to simulate.
    # You can start with a small number and adjust as needed for your simulation.
    number_of_news_events = 10
        

    social_media_node = random.choice(list(customer_network.nodes))
    social_media_type = random.choice(['positive', 'negative']) # Randomly choose the nature of social media influence
    spread_information(customer_network,social_media_node,impact_factor=0.1,information_type=social_media_type)
    log_trust_levels(customer_network, "After Spreading Information")

    # After spreading negative information, spread positive information
    #spread_positive_information(customer_network, positive_intensity, positive_frequency)
    


     # Apply external influences based on node degree
    base_strength = 0.05  # This is the base impact strength you want to apply
    for node in customer_network.nodes():
        customer = customer_network.nodes[node]['customer']
        degree = customer_network.degree(node)
        # Adjust the strength of the influence based on the node's degree
        degree_factor = degree / (1 + max(dict(customer_network.degree()).values()))
        influence_strength = random.uniform(-base_strength, base_strength) * degree_factor
        customer.trust_level += influence_strength
        customer.trust_level = max(min(customer.trust_level, 1.0), 0.0)  # Ensure within bounds
        log_trust_levels(customer_network, "After External Influences")
        log_trust_changes(initial_trust_levels, customer_network, "After External Influences")
    
    

    customer_actions(customer_network, banks, tau, sigma)
    log_trust_levels(customer_network, "After Customer Actions")
    log_trust_changes(initial_trust_levels, customer_network, "After Customer Reactions")
    
    
    # Here is where you might call your feedback loop function. For example:
   # Propagate the impact of customer decisions through the network
    

    # Parameters for customer decision propagation
    base_impact_factor = 0.00000000002  # Starting impact factor for the decision propagation
    depth_limit = 3  # How many degrees away from the node the impact should propagate
    dampening_factor = 0.9  # The reduction in impact per unit trust level

    
    for node in customer_network.nodes():
       propagate_customer_decisions(customer_network, node, base_impact_factor, depth_limit, dampening_factor)

    log_trust_levels(customer_network, "After Feedback Loops")


    # Tally and print actions
    tally_customer_actions(customer_network)

   
     # Identify clusters within the network
    clusters = nx_comm.greedy_modularity_communities(customer_network)
    
    # Analyze the clusters
    for cluster in clusters:
        internal_edges = customer_network.subgraph(cluster).number_of_edges()
        external_edges = sum(1 for node in cluster for neighbor in customer_network.neighbors(node) if neighbor not in cluster)
        print(f"Cluster with {len(cluster)} nodes, {internal_edges} internal edges and {external_edges} external edges")

    
    # Apply positive and negative news events
    apply_news_events(customer_network, number_of_news_events)
    log_trust_levels(customer_network, "After News Event")
    
    # Natural recovery of trust levels
    for node in customer_network.nodes():
        customer = customer_network.nodes[node]['customer']
        customer.trust_level = min(customer.trust_level + natural_recovery_rate, 1.0)

    log_trust_levels(customer_network, "After Natural Recovery")

    iterations = 100



    run_test_simulation(iterations)
   
    visualize_network_trust_levels(customer_network)


# Run the simulation
run_simulation()





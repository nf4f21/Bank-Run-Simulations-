import matplotlib.pyplot as plt
import numpy as np
from financial_manager import FinancialManager
class Bank:

    def __init__(self, risk_strategy, financial_manager, network_degree, tau, initial_balance=1000):
        self.financial_manager = financial_manager
        self.risk_strategy = risk_strategy
        self.network_degree = network_degree  # Ensure this is defined before calling update_bank_status()
        self.isInsolvent = False
        self.isBankrupt = False
        self.balance_sheet = risk_strategy  # Assuming initial value based on the risk strategy
        self.balance_sheet_size = initial_balance  # Initialize with a default value
        self.dividend_rate = 0.01 * self.risk_strategy * 0.1  # Example calculation

        # Initialize utility and trust level to 0; they will be set properly in update_bank_status()
        self.utility = 0
        self.trust_level = 0
        self.update_bank_status()  # Now safe to call

        self.customer_count = 0  # Track the number of customers
        self.total_withdrawn = 0  # Track total amount withdrawn
        self.customers = [] #list of customers in a bank 

        self.customer_activity = {}  # Track customer activity

        self.total_liabilities = 0
        self.tau = tau  # Trust threshold


    def calculate_profit(self):
        # the profit is calculated based on the risk strategy => the higher the risk, the higher the profit (or loss) => directly proportional
        return self.risk_strategy
    
    def adapt_strategy(self, other_bank, sigma= 0.01, pmut= 0.0005):
        if other_bank.profit > self.profit:
            self.risk_strategy += sigma * (other_bank.risk_strategy - self.risk_strategy)  # the risk strategy is adjusted based on the other bank's risk strategy
            
        # mutation
        self.risk_strategy += np.random.uniform(-pmut, pmut)  # the risk strategy is adjusted based on a random mutation
        self.risk_strategy = min(max(self.risk_strategy, 0), 1)  # the risk strategy is adjusted to be within the range [0, 1]

    def calculate_fragility(self):
        # the fragility is calculated based on the risk strategy => the higher the risk, the higher the fragility => directly proportional
        return self.risk_strategy
    
    def update_insolvency(self):
        # update the insolvency status of the bank
        self.isInsolvent = True
        self.trust_level = self.calculate_trust_level()  # Recalculate trust level based on new status


    def update_bankruptcy(self):
        # update the bankruptcy status of the bank
        self.isBankrupt = True
        self.risk_strategy = 0  # set the risk strategy to 0
        self.trust_level = self.calculate_trust_level()  # Trust drops to 0 if bankrupt
        print("bank at node  ")

    def adjust_risk_strategy(self, eta, k):
        # adjust the risk strategy of the bank
        self.risk_strategy *= max((1 - eta / k), 0)  # the risk strategy is adjusted based on the eta and the degree of the bank
    
    

    def update_balance_sheet_size(self,network_degree):
        #update balance sheet size based on value
        self.balance_sheet_size = self.risk_strategy * network_degree

    def pay_dividend(self):
        # pay dividend to the shareholders
        if not self.isInsolvent:
            return self.balance_sheet_size * self.dividend_rate
        else:
            # No dividends if the bank is insolvent
            return 0
        
    def calculate_trust_level(self):
        # Trust level now also considers the bank's utility
        if self.isBankrupt:
            return 0
        elif self.isInsolvent:
            return 0.25 * self.utility
        else:
            size_factor = np.log(self.network_degree + 1)
            return size_factor * self.utility
        
    def upddate_bank_status(self):
        self.utility = self.financial_manager.calculate_utility(self)
        self.trust_level = self.calculate_trust_level()
    
    def update_bank_status(self):
        # Dynamic calculation based on current state
        self.utility = self.financial_manager.calculate_utility(self)
        self.trust_level = self.calculate_trust_level()

    def handle_withdrawal(self, amount):
        if self.balance_sheet_size is None:
            print("Error: Bank balance sheet size is not initialized.")
            return False
        if self.balance_sheet_size >= amount:
            self.balance_sheet_size -= amount
            print(f"Withdrawal successful: New balance sheet size: {self.balance_sheet_size}")
            return True
        else:
            print("Insufficient funds for withdrawal.")
            return False

    def adjust_customer_count(self, delta):
        # Adjust the customer count up or down
        self.customer_count += delta

    def handle_deposit(self, amount, customer_id=None):
        self.balance_sheet_size += amount
        print(f"Handled deposit of ${amount}. Updated balance sheet size: {self.balance_sheet_size}")
        
        # Record the deposit action from the customer
        if customer_id is not None:
            self.record_customer_activity(customer_id, 'deposit', amount)
        
        # Optionally, increase the customer count or perform other actions
        self.adjust_customer_count(1)

    def evaluate_status(self):
        if self.isBankrupt:
            return "Bankrupt"
        elif self.isInsolvent:
            return "Insolvent"
        elif self.utility < 0.25:  # Example threshold for risk
            return "At Risk"
        else:
            return "Healthy"
        
    def handle_withdrawal(self, amount):
        print(f"Attempting withdrawal: Amount = {amount}, Current Balance Sheet Size = {self.balance_sheet_size}")
        # Check if balance_sheet_size has not been initialized
        if self.balance_sheet_size is None:
            print("Error: balance_sheet_size is uninitialized, setting to zero.")
            self.balance_sheet_size = 1000

        print(f"Attempting withdrawal: Amount = {amount}, Current Balance Sheet Size = {self.balance_sheet_size}")

        if self.balance_sheet_size >= amount:
            self.balance_sheet_size -= amount
            print(f"Withdrawal successful: New balance sheet size: {self.balance_sheet_size}")
            return True
        else:
            print("Insufficient funds for withdrawal.")
            return False



        
    def record_customer_activity(self, customer_id, activity_type, amount):
        if customer_id not in self.customer_activity:
            self.customer_activity[customer_id] = {'withdrawals': 0, 'deposits': 0}
        
        if activity_type == 'withdrawal':
            self.customer_activity[customer_id]['withdrawals'] += amount
        elif activity_type == 'deposit':
            self.customer_activity[customer_id]['deposits'] += amount


    def update_trust_level_based_on_customers(self, average_customer_trust):
        # Trust level might be a weighted average of bank's current trust level and the average customer trust
        self.trust_level = (self.trust_level + average_customer_trust) / 2
        
    def respond_to_customer_behavior(self, num_withdrawals):
        if num_withdrawals > self.customer_count * 0.1:  # If more than 10% of customers withdraw
            self.isInsolvent = True
            self.update_trust_level_based_on_customers(0)  # Trust drops due to mass withdrawals

    def adjust_customer_count(self, delta):
        self.customer_count += delta
        # Make sure to handle the case where the customer count should not go below zero
        self.customer_count = max(self.customer_count, 0)


    def evaluate_trust_level(self):
        # Calculate trust level based on customer activity
        total_withdrawals = sum(v['withdrawals'] for v in self.customer_activity.values())
        total_deposits = sum(v['deposits'] for v in self.customer_activity.values())

        # Assuming more withdrawals compared to deposits indicates lower trust
        if self.balance_sheet_size > 0:  # Check if balance sheet size is greater than zero
            self.trust_level = max(0.0, self.trust_level - (total_withdrawals - total_deposits) / self.balance_sheet_size)
        else:
            # Define default behavior when balance sheet size is zero
            self.trust_level = max(0.0, self.trust_level - (total_withdrawals - total_deposits) * 0.01)  # Example adjustment

        print(f"Updated trust level to {self.trust_level}")



    def update_liabilities(self, amount):
        self.total_liabilities += amount
        print(f"Updated total liabilities to {self.total_liabilities}")



'''
     # Example usage:
    bank = Bank(risk_strategy=0.00001)
    profit = bank.calculate_profit()
    fragility = bank.calculate_fragility()
    print(f"Profit: {profit}, Fragility: {fragility}")
'''
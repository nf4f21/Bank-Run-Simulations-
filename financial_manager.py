import numpy as np
class FinancialManager:
    def __init__(self):
        self.Cb = 0  # Cumulative cost of bankruptcy 
        self.Cv = 0  # Cumulative cost of intervention
        self.Ca = 0  # Cumulative cost of asset-write down 
        self.B = 0   # Cumulative benefit
        

    def calculate_balance_sheet_size(self, risk_strategy, network_degree):
        # Example calculation, adjust according to your model's specifics
        balance_sheet_size = risk_strategy * network_degree
        return balance_sheet_size

    '''
    def update_for_bankruptcy(self, risk_strategy, network_degree):
        balance_sheet_size = self.calculate_balance_sheet_size(risk_strategy, network_degree)
        self.Cb += balance_sheet_size
        print(f"Updating for bankruptcy with balance sheet size: {balance_sheet_size}")
    '''
    def update_for_bankruptcy(self,bank):
        balance_sheet_size = bank.balance_sheet_size
        systemic_importance_factor = np.log1p(bank.balance_sheet_size)
        self.Cb += balance_sheet_size * systemic_importance_factor
        print(f"Updating for bankruptcy with balance sheet size: {balance_sheet_size}")

    '''
    def update_for_bankruptcy(self,bank):
        balance_sheet_size = bank.balance_sheet_size
        self.Cb += balance_sheet_size 
        print(f"Updating for bankruptcy with balance sheet size: {balance_sheet_size}")
    '''

    def update_for_bailout(self,bank):
        # Bailouts may have additional costs compared to bankruptcies
        balance_sheet_size = bank.balance_sheet_size
        bailout_cost = 1.2 * balance_sheet_size * np.log1p(balance_sheet_size)
        self.Cv += bailout_cost
        print(f"Updating for bailout with balance sheet size: {balance_sheet_size}")

    '''
   def update_for_bailout(self,bank):
        balance_sheet_size = bank.balance_sheet_size
        self.Cv += balance_sheet_size
        print(f"Updating for bailout with balance sheet size: {balance_sheet_size}")

    '''
    def update_for_asset_write_down(self,bank):
        # For asset write-down, you may use a fraction of the balance sheet size
        balance_sheet_size = bank.balance_sheet_size
        asset_write_down_cost = 0.5 * balance_sheet_size
        self.Ca += asset_write_down_cost
        print(f"Updating for asset write down with balance sheet size: {balance_sheet_size}")
        
    '''
    def update_for_benefit(self, risk_strategy, network_degree):
        balance_sheet_size = self.calculate_balance_sheet_size(risk_strategy, network_degree)
        self.B += balance_sheet_size
        print(f"Updating for benefit with balance sheet size: {balance_sheet_size}")
    '''
    def calculate_utility(self,bank):
        dividends = bank.pay_dividend()
        social_cost = self.Cb + self.Cv + self.Ca
        utility = dividends - social_cost
        return utility
    
    def update_for_benefit(self,bank):
        balance_sheet_size = bank.balance_sheet_size
        self.B += balance_sheet_size
        print(f"Updating for benefit with balance sheet size: {balance_sheet_size}")    

    def calculate_social_cost(self, alpha=5, beta=0.09):
        return -self.Cb - self.Cv - alpha * self.Ca + beta * self.B
    
    def process_bankruptcy(self, bank, network_degree):
        # Calculate balance sheet size directly here (example calculation)
        bank_balance_sheet_size = bank.risk_strategy * network_degree
        
        # Update the bank instance directly
        bank.update_balance_sheet_size(bank_balance_sheet_size)
        
        # Update financial manager's metrics
        self.Cb += bank_balance_sheet_size
        print(f"Processed bankruptcy for {bank}. New balance sheet size: {bank_balance_sheet_size}")


    def process_bailout(self, bank, network_degree):
        # Similar calculation as bankruptcy
        bank_balance_sheet_size = self.calculate_balance_sheet_size(bank.risk_strategy, network_degree)
        
        # Directly update the bank instance
        bank.update_balance_sheet_size(bank_balance_sheet_size + 1)  # Assuming bailout increases balance sheet
        
        # Update financial metrics within FinancialManager
        self.Cv += bank_balance_sheet_size
        print(f"Processed bailout for {bank}. Updated balance sheet size: {bank.balance_sheet_size}")



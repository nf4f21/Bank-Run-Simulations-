import unittest
from bank import Bank
from customer import Customer
from financial_manager import FinancialManager

class TestBankCustomerInteractions(unittest.TestCase):
    def setUp(self):
        # Setting up objects and their initial state
        self.financial_manager = FinancialManager()
        # Example test setup
        self.bank = Bank(risk_strategy=0.5, financial_manager=FinancialManager(), network_degree=5, tau=0.5, initial_balance=5000)
        self.customer = Customer(bank=self.bank, risk_tolerance=0 ,savings=1000, trust_level=0.2)

    def test_customer_withdrawal_impacts_bank(self):
        # Test that customer withdrawals properly reduce the bank's balance sheet size
        initial_balance = self.bank.balance_sheet_size
        withdrawal_amount = 200
        self.customer.withdraw_savings(withdrawal_amount)
        self.assertEqual(self.bank.balance_sheet_size, initial_balance - withdrawal_amount, "Bank's balance did not update correctly after withdrawal.")

    def test_bank_response_to_risk(self):
        # Ensuring the bank adjusts its risk strategy or insolvency status based on withdrawals
        large_withdrawal = 800
        self.customer.withdraw_savings(large_withdrawal)
        self.assertTrue(self.bank.isInsolvent, "Bank did not become insolvent after large withdrawal affecting balance sheet significantly.")

if __name__ == '__main__':
    unittest.main()

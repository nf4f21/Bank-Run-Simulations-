import unittest
from bank import Bank
from debugging_class import DebuggingClass
class TestBankMethods(unittest.TestCase):

    def test_adapt_strategy_increases_strategy(self):
        bank = Bank(risk_strategy=0.5)
        bank.adapt_strategy(peer_strategy=0.6)
        self.assertTrue(bank.risk_strategy > 0.5)

    def test_adapt_strategy_decreases_with_lower_peer_strategy(self):
        bank = Bank(risk_strategy=0.5)
        bank.adapt_strategy(peer_strategy=0.4)
        # Assuming the strategy only adapts when peer's is higher, it should not change
        self.assertEqual(bank.risk_strategy, 0.5)

    def test_adapt_strategy_stays_within_bounds(self):
        bank = Bank(risk_strategy=0.01)
        bank.adapt_strategy(peer_strategy=1.0, sigma=1, pmut=0.5)  # Extreme values to test bounds
        self.assertTrue(0 <= bank.risk_strategy <= 1)

if __name__ == '__main__':
    unittest.main()

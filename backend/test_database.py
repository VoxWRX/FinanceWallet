import unittest
import os
from database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Use a temporary file for testing
        self.db_path = "test_db.sqlite3"
        self.db = DatabaseManager(self.db_path)
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    def test_categories_crud(self):
        # Create
        cat_id = self.db.add_category("Groceries", "Expense", "#FF0000")
        self.assertIsNotNone(cat_id)
        
        # Read
        categories = self.db.get_categories()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]['name'], "Groceries")
        
        # Update
        self.db.update_category(cat_id, name="Food")
        updated_cat = self.db.get_categories()[0]
        self.assertEqual(updated_cat['name'], "Food")
        
        # Delete
        success = self.db.delete_category(cat_id)
        self.assertTrue(success)
        self.assertEqual(len(self.db.get_categories()), 0)

    def test_transactions_crud(self):
        cat_id = self.db.add_category("Salary", "Income", "#00FF00")
        
        # Create
        tx_id = self.db.add_transaction("October Salary", 5000.0, "2023-10-01", "Monthly Salary", cat_id, transaction_author="John")
        self.assertIsNotNone(tx_id)
        
        # Read
        txs = self.db.get_transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]['amount'], 5000.0)
        self.assertEqual(txs[0]['name'], "October Salary")
        self.assertEqual(txs[0]['transaction_author'], "John")
        
        # Update
        self.db.update_transaction(tx_id, amount=5200.0)
        updated_txs = self.db.get_transactions()
        self.assertEqual(updated_txs[0]['amount'], 5200.0)
        
        # Delete
        self.db.delete_transaction(tx_id)
        self.assertEqual(len(self.db.get_transactions()), 0)

    def test_saving_goals_crud(self):
        # Create
        goal_id = self.db.add_goal("New Car", 20000.0, 1500.0, "2025-01-01")
        self.assertIsNotNone(goal_id)
        
        # Read
        goals = self.db.get_goals()
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0]['target_amount'], 20000.0)
        
        # Update
        self.db.update_goal(goal_id, current_amount=2000.0)
        updated_goals = self.db.get_goals()
        self.assertEqual(updated_goals[0]['current_amount'], 2000.0)
        
        # Delete
        self.db.delete_goal(goal_id)
        self.assertEqual(len(self.db.get_goals()), 0)
        
    def test_data_aggregation(self):
        # Setup data
        inc_cat = self.db.add_category("Salary", "Income")
        exp_cat1 = self.db.add_category("Groceries", "Expense")
        exp_cat2 = self.db.add_category("Rent", "Expense")
        
        self.db.add_transaction("Paycheck", 5000, "2023-10-01", "Salary", inc_cat)
        self.db.add_transaction("House Rent", 1000, "2023-10-02", "Rent", exp_cat2)
        self.db.add_transaction("Walmart", 200, "2023-10-03", "Groceries", exp_cat1)
        self.db.add_transaction("Whole Foods", 300, "2023-10-15", "More Groceries", exp_cat1)
        
        # Test total balance
        # Income 5000, Expense 1500 => Balance 3500
        self.assertEqual(self.db.get_total_balance(), 3500.0)
        
        # Test expenses by category
        exp_by_cat = self.db.get_expenses_by_category()
        self.assertEqual(len(exp_by_cat), 2)
        # Should be ordered by total DESC (Rent: 1000, Groceries: 500)
        self.assertEqual(exp_by_cat[0]['name'], "Rent")
        self.assertEqual(exp_by_cat[0]['total'], 1000.0)
        self.assertEqual(exp_by_cat[1]['name'], "Groceries")
        self.assertEqual(exp_by_cat[1]['total'], 500.0)
        
        # Test income vs expense
        inc_vs_exp = self.db.get_income_vs_expense()
        self.assertEqual(inc_vs_exp['Income'], 5000.0)
        self.assertEqual(inc_vs_exp['Expense'], 1500.0)

if __name__ == '__main__':
    unittest.main()

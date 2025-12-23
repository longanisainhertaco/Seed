import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import database
from app.models import Seed, Task, TaskType, TaskStatus, Inventory, InventoryAdjustment


class TestDatabase(unittest.TestCase):
    """Test database operations."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        database.DATABASE_PATH = cls.test_db.name
        database.init_database()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        os.unlink(cls.test_db.name)

    def setUp(self):
        """Clear database before each test."""
        with database.get_session() as session:
            session.query(InventoryAdjustment).delete()
            session.query(Task).delete()
            session.query(Inventory).delete()
            session.query(Seed).delete()
            session.flush()

    def test_create_and_get_seed(self):
        """Test creating and retrieving a seed."""
        seed = Seed(
            type="Vegetable",
            name="Carrot",
            packets_made=5,
            seed_source="Garden Store"
        )
        seed_id = database.create_seed(seed)
        self.assertIsNotNone(seed_id)

        retrieved = database.get_seed_by_id(seed_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['name'], "Carrot")
        self.assertEqual(retrieved['type'], "Vegetable")

    def test_get_all_seeds(self):
        """Test retrieving all seeds."""
        seed1 = Seed(type="Vegetable", name="Carrot")
        seed2 = Seed(type="Herb", name="Basil")
        database.create_seed(seed1)
        database.create_seed(seed2)

        seeds = database.get_all_seeds()
        self.assertEqual(len(seeds), 2)

    def test_update_seed(self):
        """Test updating a seed."""
        seed = Seed(type="Vegetable", name="Carrot")
        seed_id = database.create_seed(seed)

        database.update_seed(seed_id, {'name': 'Purple Carrot'})
        updated = database.get_seed_by_id(seed_id)
        self.assertEqual(updated['name'], 'Purple Carrot')

    def test_delete_seed(self):
        """Test deleting a seed."""
        seed = Seed(type="Vegetable", name="Carrot")
        seed_id = database.create_seed(seed)

        database.delete_seed(seed_id)
        deleted = database.get_seed_by_id(seed_id)
        self.assertIsNone(deleted)

    def test_create_task(self):
        """Test creating a task."""
        seed = Seed(type="Vegetable", name="Carrot")
        seed_id = database.create_seed(seed)

        task = Task(
            seed_id=seed_id,
            task_type=TaskType.PACK,
            status=TaskStatus.TODO,
            description="Pack carrot seeds"
        )
        task_id = database.create_task(task)
        self.assertIsNotNone(task_id)

        tasks = database.get_tasks_by_seed(seed_id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['task_type'], TaskType.PACK)
        self.assertEqual(tasks[0]['priority'], "Medium")

    def test_inventory_operations(self):
        """Test inventory operations."""
        seed = Seed(type="Vegetable", name="Carrot")
        seed_id = database.create_seed(seed)

        inventory = database.get_or_create_inventory(seed_id)
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory['seed_id'], seed_id)

        database.update_inventory(seed_id, {
            'current_amount': '50 packets',
            'buy_more': True
        })

        updated = database.get_or_create_inventory(seed_id)
        self.assertEqual(updated['current_amount'], '50 packets')
        self.assertTrue(updated['buy_more'])

    def test_inventory_adjustments(self):
        """Test inventory adjustment tracking."""
        seed = Seed(type="Vegetable", name="Carrot")
        seed_id = database.create_seed(seed)

        adjustment = InventoryAdjustment(
            seed_id=seed_id,
            adjustment_type="Addition",
            amount_change="20 packets",
            reason="New shipment"
        )
        adj_id = database.create_inventory_adjustment(adjustment)
        self.assertIsNotNone(adj_id)

        adjustments = database.get_inventory_adjustments(seed_id)
        self.assertEqual(len(adjustments), 1)
        self.assertEqual(adjustments[0]['adjustment_type'], "Addition")


if __name__ == '__main__':
    unittest.main()

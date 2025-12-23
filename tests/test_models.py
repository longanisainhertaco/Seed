import unittest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Seed, Task, Inventory, InventoryAdjustment, TaskType, TaskStatus, TaskPriority


class TestModels(unittest.TestCase):
    """Test model classes."""

    def test_seed_creation(self):
        """Test Seed model creation."""
        seed = Seed(
            type="Vegetable",
            name="Tomato",
            packets_made=10,
            seed_source="Local Farm",
            amount_text="50g"
        )
        self.assertEqual(seed.type, "Vegetable")
        self.assertEqual(seed.name, "Tomato")
        self.assertEqual(seed.packets_made, 10)
        self.assertEqual(seed.seed_source, "Local Farm")
        self.assertEqual(seed.amount_text, "50g")
        self.assertIsNotNone(seed.created_at)
        self.assertIsNotNone(seed.updated_at)

    def test_task_creation(self):
        """Test Task model creation."""
        task = Task(
            seed_id=1,
            task_type=TaskType.PACK,
            status=TaskStatus.TODO,
            description="Pack tomato seeds"
        )
        self.assertEqual(task.seed_id, 1)
        self.assertEqual(task.task_type, TaskType.PACK)
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.priority, TaskPriority.MEDIUM)
        self.assertEqual(task.description, "Pack tomato seeds")
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)

    def test_inventory_creation(self):
        """Test Inventory model creation."""
        inventory = Inventory(
            seed_id=1,
            current_amount="100 packets",
            buy_more=True,
            extra=False,
            notes="Low stock"
        )
        self.assertEqual(inventory.seed_id, 1)
        self.assertEqual(inventory.current_amount, "100 packets")
        self.assertTrue(inventory.buy_more)
        self.assertFalse(inventory.extra)
        self.assertEqual(inventory.notes, "Low stock")

    def test_inventory_adjustment_creation(self):
        """Test InventoryAdjustment model creation."""
        adjustment = InventoryAdjustment(
            seed_id=1,
            adjustment_type="Addition",
            amount_change="50 packets",
            reason="New delivery"
        )
        self.assertEqual(adjustment.seed_id, 1)
        self.assertEqual(adjustment.adjustment_type, "Addition")
        self.assertEqual(adjustment.amount_change, "50 packets")
        self.assertEqual(adjustment.reason, "New delivery")


if __name__ == '__main__':
    unittest.main()

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.task_service import calculate_task_metrics
from app.models import Task, TaskStatus, TaskType


class TestTaskService(unittest.TestCase):
    """Test task service functions."""

    def test_calculate_task_metrics_empty(self):
        """Test metrics calculation with no tasks."""
        from unittest.mock import patch

        with patch('app.services.task_service.get_all_tasks', return_value=[]):
            metrics = calculate_task_metrics()
            self.assertEqual(metrics['total'], 0)
            self.assertEqual(metrics['done'], 0)
            self.assertEqual(metrics['completion_percentage'], 0)

    def test_calculate_task_metrics_with_tasks(self):
        """Test metrics calculation with tasks."""
        from unittest.mock import patch
        from datetime import datetime, timedelta

        today = datetime.now()
        yesterday = (today - timedelta(days=1)).isoformat()
        tomorrow = (today + timedelta(days=1)).isoformat()

        mock_tasks = [
            {'status': TaskStatus.DONE, 'due_date': tomorrow},
            {'status': TaskStatus.TODO, 'due_date': yesterday},
            {'status': TaskStatus.IN_PROGRESS, 'due_date': tomorrow},
            {'status': TaskStatus.TODO, 'due_date': today.date().isoformat()},
        ]

        with patch('app.services.task_service.get_all_tasks', return_value=mock_tasks):
            metrics = calculate_task_metrics()
            self.assertEqual(metrics['total'], 4)
            self.assertEqual(metrics['done'], 1)
            self.assertEqual(metrics['in_progress'], 1)
            self.assertEqual(metrics['pending'], 2)
            self.assertEqual(metrics['overdue'], 1)
            self.assertEqual(metrics['due_today'], 1)
            self.assertEqual(metrics['completion_percentage'], 25.0)


if __name__ == '__main__':
    unittest.main()

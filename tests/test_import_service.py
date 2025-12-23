import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.import_service import import_seeds_from_excel


class TestImportService(unittest.TestCase):
    """Tests for import service column mapping validation."""

    def _create_temp_excel(self, data):
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        df = pd.DataFrame(data)
        df.to_excel(tmp_file.name, index=False)
        self.addCleanup(lambda: os.path.exists(tmp_file.name) and os.remove(tmp_file.name))
        return tmp_file.name

    def test_missing_required_mapping(self):
        """Ensure missing required mappings return validation errors and stop import."""
        file_path = self._create_temp_excel({'Type': ['Herb'], 'Name': ['Basil']})
        mapping = {'Type': 'Type', 'Name': None}

        with patch('app.services.import_service.create_seed') as mock_create_seed, \
                patch('app.services.import_service.get_or_create_inventory') as mock_inventory:
            result = import_seeds_from_excel(file_path, mapping)

        self.assertFalse(result['success'])
        self.assertIn("Mapping for required field 'Name' is missing.", result['mapping_errors'])
        self.assertEqual(result['total_rows'], 1)
        mock_create_seed.assert_not_called()
        mock_inventory.assert_not_called()

    def test_invalid_column_mapping(self):
        """Ensure mapping to a missing column is surfaced before import."""
        file_path = self._create_temp_excel({'Type': ['Herb'], 'Name': ['Basil']})
        mapping = {'Type': 'MissingCol', 'Name': 'Name'}

        with patch('app.services.import_service.create_seed') as mock_create_seed, \
                patch('app.services.import_service.get_or_create_inventory') as mock_inventory:
            result = import_seeds_from_excel(file_path, mapping)

        self.assertFalse(result['success'])
        self.assertIn("Column 'MissingCol' was not found for 'Type'.", result['mapping_errors'])
        self.assertEqual(result['total_rows'], 1)
        mock_create_seed.assert_not_called()
        mock_inventory.assert_not_called()

    def test_duplicate_column_mapping_flagged(self):
        """Ensure duplicate column mappings are rejected to avoid ambiguous imports."""
        file_path = self._create_temp_excel({'Type': ['Herb'], 'Name': ['Basil'], 'Extra': ['x']})
        mapping = {'Type': 'Type', 'Name': 'Name', 'packets_made': 'Type'}

        result = import_seeds_from_excel(file_path, mapping)

        self.assertFalse(result['success'])
        self.assertIn("Column 'Type' is mapped to multiple fields. Please choose unique columns.", result['mapping_errors'])


if __name__ == '__main__':
    unittest.main()

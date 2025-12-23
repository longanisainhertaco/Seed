import pandas as pd
from typing import List, Dict, Any
import logging
from datetime import datetime
from app.models import Seed
from app.database import create_seed, get_or_create_inventory

logger = logging.getLogger(__name__)


REQUIRED_FIELDS = ['Type', 'Name']
SUPPORTED_FIELDS = [
    'Type',
    'Name',
    'packets_made',
    'seed_source',
    'date_ordered',
    'date_finished',
    'date_cataloged',
    'date_ran_out',
    'amount_text'
]


def import_seeds_from_excel(file_path: str, mapping: Dict[str, str]) -> Dict[str, Any]:
    """Import seeds from an Excel file using an explicit column mapping."""
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()

        logger.info(f"Reading Excel file: {file_path}")
        logger.info(f"Columns found: {df.columns.tolist()}")

        mapping_errors: List[str] = []

        if not mapping:
            mapping_errors.append("No column mappings were provided.")

        for required_field in REQUIRED_FIELDS:
            if not mapping.get(required_field):
                mapping_errors.append(f"Mapping for required field '{required_field}' is missing.")

        # Avoid mapping the same source column multiple times
        provided_columns = [col for col in mapping.values() if col]
        duplicates = {col for col in provided_columns if provided_columns.count(col) > 1}
        if duplicates:
            for dup in duplicates:
                mapping_errors.append(f"Column '{dup}' is mapped to multiple fields. Please choose unique columns.")

        for target_field, source_column in mapping.items():
            if not source_column:
                continue
            if source_column not in df.columns:
                mapping_errors.append(f"Column '{source_column}' was not found for '{target_field}'.")

        if mapping_errors:
            return {
                'success': False,
                'error': 'Mapping validation failed',
                'mapping_errors': mapping_errors,
                'imported_count': 0,
                'total_rows': len(df),
                'errors': []
            }

        imported_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                def get_cell(field: str):
                    column = mapping.get(field)
                    if not column:
                        return None
                    return row.get(column)

                seed = Seed(
                    type=str(get_cell('Type') or ''),
                    name=str(get_cell('Name') or ''),
                    packets_made=int(get_cell('packets_made') or 0) if pd.notna(get_cell('packets_made')) else 0,
                    seed_source=str(get_cell('seed_source') or '') if pd.notna(get_cell('seed_source')) else '',
                    date_ordered=str(get_cell('date_ordered') or '') if pd.notna(get_cell('date_ordered')) else None,
                    date_finished=str(get_cell('date_finished') or '') if pd.notna(get_cell('date_finished')) else None,
                    date_cataloged=str(get_cell('date_cataloged') or '') if pd.notna(get_cell('date_cataloged')) else None,
                    date_ran_out=str(get_cell('date_ran_out') or '') if pd.notna(get_cell('date_ran_out')) else None,
                    amount_text=str(get_cell('amount_text') or '') if pd.notna(get_cell('amount_text')) else '',
                )

                seed_id = create_seed(seed)
                get_or_create_inventory(seed_id)
                imported_count += 1

            except Exception as e:
                error_msg = f"Row {index + 2}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        return {
            'success': True,
            'imported_count': imported_count,
            'total_rows': len(df),
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Failed to import Excel file: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'imported_count': 0,
            'total_rows': 0,
            'errors': [],
            'mapping_errors': []
        }

import pandas as pd
from typing import List, Dict, Any
import logging
from datetime import datetime
from app.models import Seed
from app.database import create_seed, get_or_create_inventory

logger = logging.getLogger(__name__)


def import_seeds_from_excel(file_path: str) -> Dict[str, Any]:
    """Import seeds from an Excel file."""
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Reading Excel file: {file_path}")
        logger.info(f"Columns found: {df.columns.tolist()}")

        expected_columns = {
            'Type', 'Name', 'packets_made', 'seed_source',
            'date_ordered', 'date_finished', 'date_cataloged',
            'date_ran_out', 'amount_text'
        }

        df.columns = df.columns.str.strip()
        available_columns = set(df.columns)

        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().replace(' ', '_')
            if col_lower in ['type', 'seed_type']:
                column_mapping[col] = 'Type'
            elif col_lower in ['name', 'seed_name']:
                column_mapping[col] = 'Name'
            elif col_lower in ['packets_made', 'packets']:
                column_mapping[col] = 'packets_made'
            elif col_lower in ['seed_source', 'source']:
                column_mapping[col] = 'seed_source'
            elif col_lower in ['date_ordered', 'ordered']:
                column_mapping[col] = 'date_ordered'
            elif col_lower in ['date_finished', 'finished']:
                column_mapping[col] = 'date_finished'
            elif col_lower in ['date_cataloged', 'cataloged']:
                column_mapping[col] = 'date_cataloged'
            elif col_lower in ['date_ran_out', 'ran_out']:
                column_mapping[col] = 'date_ran_out'
            elif col_lower in ['amount_text', 'amount']:
                column_mapping[col] = 'amount_text'

        if column_mapping:
            df = df.rename(columns=column_mapping)

        imported_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                seed = Seed(
                    type=str(row.get('Type', '')),
                    name=str(row.get('Name', '')),
                    packets_made=int(row.get('packets_made', 0)) if pd.notna(row.get('packets_made')) else 0,
                    seed_source=str(row.get('seed_source', '')) if pd.notna(row.get('seed_source')) else '',
                    date_ordered=str(row.get('date_ordered', '')) if pd.notna(row.get('date_ordered')) else None,
                    date_finished=str(row.get('date_finished', '')) if pd.notna(row.get('date_finished')) else None,
                    date_cataloged=str(row.get('date_cataloged', '')) if pd.notna(row.get('date_cataloged')) else None,
                    date_ran_out=str(row.get('date_ran_out', '')) if pd.notna(row.get('date_ran_out')) else None,
                    amount_text=str(row.get('amount_text', '')) if pd.notna(row.get('amount_text')) else '',
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
            'errors': []
        }

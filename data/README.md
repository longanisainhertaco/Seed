# Sample Excel Template for Seed Library Import

This directory is where you place Excel files (.xlsx) for import.

## Required Columns

Your Excel file should have these columns:

- **Type**: Seed type (e.g., Vegetable, Herb, Flower)
- **Name**: Name of the seed
- **packets_made**: Number of packets created (numeric)
- **seed_source**: Where the seeds came from
- **date_ordered**: Date ordered (YYYY-MM-DD format)
- **date_finished**: Date packaging finished (YYYY-MM-DD format)
- **date_cataloged**: Date cataloged (YYYY-MM-DD format)
- **date_ran_out**: Date ran out of stock (YYYY-MM-DD format)
- **amount_text**: Text description of amount

## Example Data

| Type      | Name         | packets_made | seed_source  | date_ordered | date_finished | date_cataloged | date_ran_out | amount_text |
|-----------|--------------|--------------|--------------|--------------|---------------|----------------|--------------|-------------|
| Vegetable | Tomato       | 25           | Local Farm   | 2024-01-15   | 2024-02-01    | 2024-02-05     |              | 100g        |
| Herb      | Basil        | 15           | Garden Store | 2024-01-20   | 2024-02-10    |                |              | 50g         |
| Flower    | Sunflower    | 30           | Online Shop  | 2024-02-01   |               |                |              | 200g        |
| Vegetable | Carrot       | 20           | Local Farm   | 2023-12-01   | 2023-12-15    | 2023-12-20     | 2024-03-01   | 75g         |

Column names are flexible - the import service will match common variations like "seed_name" or "Name".

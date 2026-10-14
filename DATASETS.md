# Local datasets and artifacts

Training datasets, model checkpoints, serialized recommendations and submissions are intentionally omitted from GitHub.

## App data files

- data/products.parquet — FastAPI product catalog
- data/item_cooccurrence.parquet — item co-purchase data
- raw_data/items.parquet — source item metadata
- raw_data/transactions-2025-12.parquet — historical transaction data for the forecast demo

## ML notebooks

- raw_data/transaction_full_2025.parquet — full 2025 transaction history
- raw_data/event_full_2025.parquet — 2025 item view/cart events

These files are copied into the clean local working directory and explicitly ignored by Git. The complete original notebooks, submissions, and training artifacts remain available in the adjacent archival directory after cleanup.

Notebook code originated in an experimental folder structure; any remaining hard-coded paths mentioning Project or Additional Doc must be adjusted to local paths before rerunning.

Never publish customer-level histories or serialized customer recommendations without explicit data redistribution permission.

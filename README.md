# DuplicateSiteCreator

DuplicateSiteCreator is an application that duplicates public storefront data into a clean template for small merchants. The project is built in Python and is organised into modules for scraping, store generation, pricing, dropshipping, inventory sync, and a local GUI.

## Getting started
1. Install project dependencies with `pip install -r requirements.txt` if a requirements file is provided, or install modules as needed (SQLAlchemy, pydantic, requests, beautifulsoup4, jinja2).
2. Adjust configuration values in `config.yaml` as needed. A SQLite database URL and basic logging options are included by default.
3. Initialise the database tables and start the bootstrap sequence:
   ```bash
   python main.py
   ```

## Project layout
- `core/config` – configuration loader utilities.
- `core/logging` – logging helpers.
- `core/db` – database setup, initialization, and repositories.
- `core/models` – SQLAlchemy and Pydantic data models.
- `core/scraper` – scraping utilities and orchestrator.
- `core/storegen` – static store builder and exporter.
- `core/pricing` – pricing rules and engine.
- `core/dropship` – supplier routing and order processing.
- `core/inventory` – inventory sync hooks.
- `app` – GUI entry point and view/controller placeholders.

## Notes
- The scraping utilities are intentionally lightweight and should respect the terms of service of the target sites.
- The current GUI is a placeholder; future work will add real screens and interactions.

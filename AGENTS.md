Duplication Site Creator – Codex Agent Instructions
Overview

This repository implements a duplication‑site creator and dropshipping automation system. The goal is to take the URL of an existing e‑commerce site, scrape its publicly visible product data, generate a new storefront using a clean template and adjusted pricing, and automate order fulfilment through dropshipping. All modules are developed in Python. The system consists of a scraping engine, site generator, pricing engine, dropshipping automation, inventory synchronisation, and a local GUI.

Codex will build this project incrementally. It should always follow these instructions, adhere to the defined directory structure, and ensure that all tests pass. When in doubt, write clear, well‑documented code and verify it with unit tests.

Environment

Python version: 3.11 or later (the environment is preconfigured).

Database: SQLite for local development. SQLAlchemy is used as the ORM.

Dependencies:

requests, beautifulsoup4, lxml for web scraping.

sqlalchemy and aiosqlite for database access.

pydantic for data validation.

jinja2 for HTML template rendering.

apscheduler for background scheduling.

A GUI framework such as PyQt5, Tkinter, Kivy or Mage (choose one and install it when needed).

Additional libraries may be added if justified (e.g. Selenium for headless browser scraping).

Running tests: use pytest -q to run all tests in the tests/ directory.

Running the application

Once the core modules and GUI are implemented, you can run the application locally with:

python main.py


Early tasks will not have a functioning GUI; you should focus on building modules and getting tests to pass before integrating everything.

Repository structure

The project uses the following folder layout (already created or to be created by Codex):

/
├── app/                  # GUI and entry‑point logic
│   ├── views/            # Individual screens (dashboard, scraper, products, pricing, orders)
│   ├── controllers/      # Bridges between GUI actions and core logic
│   └── gui.py            # Main window and navigation
├── core/                 # Business logic modules
│   ├── scraper/          # Web scraping engine
│   ├── storegen/         # Static site generator
│   ├── pricing/          # Pricing rules and demand scoring
│   ├── dropship/         # Order routing to suppliers
│   ├── inventory/        # Inventory synchronisation
│   ├── config/           # Configuration loader
│   ├── logging/          # Logging wrapper
│   ├── models/           # SQLAlchemy and Pydantic models
│   ├── db/               # Database session setup and repositories
│   └── __init__.py
├── tests/                # Unit and integration tests
├── config.yaml           # YAML configuration file loaded by core/config/settings.py
├── main.py               # Application entry point
└── README.md / AGENTS.md # Project documentation and agent instructions

Development tasks

Codex should build the system step by step. Each numbered item below corresponds to a discrete task that Codex can run in isolation. After completing a task, commit the changes in its environment, verify that the associated tests pass, and move to the next task. If tests fail, fix the code and rerun them until they pass.

Repository skeleton and configuration

Create the folder structure shown above.

Add an empty __init__.py to each package directory.

Implement core/config/settings.py to load settings from config.yaml and expose helper functions such as get_db_url() and get_default_currency().

Implement core/logging/logger.py to wrap Python’s logging module and provide a get_logger(name) function that returns a configured logger.

Database setup and models

In core/db/base.py, create an SQLAlchemy engine, a SessionLocal factory, and a declarative Base class.

Define SQLAlchemy models in core/models/ for Product, Variant, Image, Supplier, Order, OrderItem, Transaction, PriceRule and Store. Use appropriate column types and relationships (foreign keys).

Create corresponding Pydantic models (e.g. in core/models/product.py) for runtime data validation.

Write a script core/db/init_db.py containing an init_db() function to create all tables. Ensure this function is called from main.py during startup.

Repository classes

Create a module core/db/repositories.py that provides classes such as ProductRepository, OrderRepository, SupplierRepository, etc. Each repository should implement methods like get_by_id, get_all, create, update, and any specialized queries (e.g. get_by_store(store_id)).

Write unit tests in tests/ to verify that these repositories perform CRUD operations correctly.

Scraper engine

Implement core/scraper/request_manager.py with a RequestManager class containing a fetch(url) method that retrieves HTML, handles timeouts, retries, headers and optional proxies.

Implement core/scraper/link_utils.py with functions such as normalize_url(href, base_url), is_same_domain(url, base_domain) and extract_links(html, base_url).

Implement core/scraper/detectors.py containing heuristics to identify product pages (e.g. presence of price tag, add‑to‑cart buttons) and optionally category pages.

Implement core/scraper/extractors.py with functions like extract_product_data(html, url) that return raw product data (name, price, description, images, category, SKU).

Implement core/scraper/orchestrator.py with a run_scrape(start_url, store_id) function that performs a breadth‑first crawl of all links on the domain, detects product pages using the detectors, extracts product data using the extractors and saves normalised records to the database via the repository layer.

Write tests with sample HTML pages to verify the detectors and extractors.

Store generator

Create a core/storegen/templates/ directory with Jinja2 templates for base.html, home.html, category.html and product.html. Keep the templates clean and avoid copying copyrighted text or logos from the scraped site.

Implement core/storegen/theme_manager.py with a function to return the path of the selected theme. Support a default theme at first.

Implement core/storegen/builder.py with a function build_store(store_id, output_dir, theme_id="default"). The builder should read products from the database for the specified store, group them into categories, render each template, and write the resulting HTML files to output_dir.

Implement core/storegen/exporter.py with functions to export the generated site to a folder or integrate with Shopify/WooCommerce in the future.

Write tests to ensure that the store generator produces files containing the expected product names and prices.

Pricing engine

Define rule models in core/pricing/rules.py, including MarginRule (with fields such as minimum margin, maximum margin, category and price band) and DemandRule (weights for factors like base price and category).

Implement core/pricing/demand_scoring.py with a compute_demand_score(product, rules) function that returns a float representing the predicted demand for a product.

Implement core/pricing/engine.py with a run_pricing(store_id) function that loads all products for a store, computes a demand score for each one, determines an appropriate margin multiplier, sets a new price field accordingly, and saves it back to the database.

Provide GUI controls (later) to run pricing and preview changes.

Dropshipping automation

Extend the data model to include Order, OrderItem and Supplier tables. Add fields to record the status and tracking number.

Create a core/dropship/adapters/base.py defining an abstract SupplierAdapter with methods place_order(order, order_item, supplier) and fetch_tracking(order, supplier).

Add one concrete adapter in core/dropship/adapters/dummy_api.py that simulates placing an order with a supplier API for testing purposes. Later, implement real adapters for live suppliers.

Implement core/dropship/router.py with a select_supplier(product_id) function that returns the appropriate supplier for a given product.

Implement core/dropship/order_processor.py with a process_pending_orders() function that retrieves pending orders, iterates through items, calls the adapter to place the order, updates the order status and saves the tracking number.

Schedule the order processor to run periodically using APScheduler (e.g. every few minutes) once integration is complete.

Inventory synchronisation

Implement core/inventory/sync_service.py with a sync_supplier_inventory(supplier_id) function that retrieves product availability and cost from the supplier (via API or scraping) and updates corresponding records in the database.

After synchronising, the service should flag products whose supplier price changed significantly so that the pricing engine can be rerun.

Use APScheduler to schedule periodic inventory synchronisation jobs.

Local GUI

Choose and install a GUI framework (e.g. PyQt5). Implement app/gui.py with a main application class that sets up the window, navigation and common layout.

Create separate view classes under app/views/ for the dashboard, scraper view, products view, pricing view, orders view and settings view. Use controllers to decouple UI events from core logic.

Provide a way to input a URL for scraping, run pricing, generate a store and view orders.

Keep the UI clean and responsive; use a grid layout with adequate spacing and clear typography.

Main application and integration

Write main.py to initialise the database (calling init_db()), start background schedulers (for orders and inventory), and launch the GUI.

Test the end‑to‑end flow: scrape a sample site, run pricing, generate a store, simulate an order and ensure the order processor calls the dummy supplier adapter.

Coding guidelines

Write clear, modular code. Separate concerns; avoid large, monolithic functions.

Follow PEP 8 style guidelines. Use descriptive names for variables, classes and functions.

Include docstrings and type hints for public functions and classes.

Write tests for new functionality. Use the tests/ directory and ensure that tests cover edge cases.

Never duplicate proprietary content. When replicating product descriptions, paraphrase them and avoid copying any copyrighted text or images. Do not copy logos or branding.

Respect websites’ robots.txt and terms of service. Implement rate limiting and user‑agent rotation in the scraper and do not attempt to bypass anti‑bot protections illegally.

Protect sensitive information. Do not store payment details or real customer data in the codebase. Use environment variables or secure payment gateways. When interacting with suppliers or customers, use tokenised or virtual card transactions and rely on third‑party processors to handle PCI compliance
litextension.com
.

Adhere to safety policies. This project must not facilitate malware, malicious scraping, copyright infringement or any other illegal or unethical activity.

Allowed commands and resources

The following commands are permitted in Codex tasks:

python <script> – run Python code.

pytest -q – run all tests quietly.

pip install <package> – install necessary Python packages (use sparingly; verify they are safe and needed).

Standard shell commands such as ls, pwd to navigate the file system.

Running scripts in scripts/ (if created later) for setup or data seeding.

Internet access is disabled by default in Codex tasks for security reasons. You should not attempt to fetch external resources unless explicitly enabled via a project configuration. When external data is required (e.g. to fetch pricing info), provide a mocked response in tests or use a test API.

What to do when uncertain

Codex should halt and ask for clarification in its UI when it encounters ambiguity that prevents progress (e.g. lacking information on a supplier’s API). When tests fail, fix the implementation before moving on. If there is a disagreement between these instructions and an individual task prompt, prefer these instructions unless the task clearly supersedes them.

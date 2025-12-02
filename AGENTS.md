Duplication Site Creator – Codex Agent Instructions
Overview
This repository implements a duplication‑site creator and dropshipping automation system. The goal is to take the URL of an existing e‑commerce site, scrape its publicly visible product data, generate a new storefront using a clean template with adjusted pricing, and automate order fulfilment through dropshipping. All modules are developed in Python.
The system consists of several components:
	• A scraping engine that can crawl a single domain and identify product pages.
	• A site generator that builds a static storefront from scraped data using clean Jinja2 templates.
	• A pricing engine that applies rule‑based and optional machine‑learning–based margin adjustments.
	• Dropshipping automation to route orders to suppliers and capture tracking information.
	• Inventory synchronisation to keep product availability and cost up to date.
	• A payments module supporting multiple payment gateways (Stripe and Shopify) with tokenised transactions.
	• Multi‑store management, so you can operate multiple storefronts from one application.
	• KPI instrumentation to monitor scraping depth, pricing uplift, order routing success and other metrics.
	• An optional machine‑learning plugin to predict optimal margins.
	• A local GUI that ties everything together in a user‑friendly desktop application.
Codex will build this project incrementally. It should always follow these instructions, adhere to the defined directory structure, and ensure that all tests pass. When in doubt, write clear, well‑documented code and verify it with unit tests.
Environment
	• Python version: 3.11 or later (the environment is preconfigured).
	• Database: SQLite for local development. SQLAlchemy is used as the ORM.
	• Dependencies:
		○ requests, beautifulsoup4, lxml for web scraping.
		○ sqlalchemy and aiosqlite for database access.
		○ pydantic for data validation.
		○ jinja2 for HTML template rendering.
		○ apscheduler for background scheduling.
		○ A GUI framework such as PyQt5, Tkinter, Kivy or Mage (choose one and install it when needed).
		○ Additional libraries may be added if justified (e.g. Selenium or Playwright for headless browser automation).
	• Running tests: Use pytest -q to run all tests in the tests/ directory.
Running the application
Once the core modules and GUI are implemented, you can run the application locally with:

python main.py
Early tasks will not have a functioning GUI; focus on building modules and getting tests to pass before integrating everything.
Repository structure
The project uses the following folder layout (to be created by Codex):

/
├── app/                  # GUI and entry‑point logic
│   ├── views/            # Individual screens (dashboard, scraper, products, pricing, orders, settings, metrics)
│   ├── controllers/      # Bridges between GUI actions and core logic
│   └── gui.py            # Main window and navigation
├── core/                 # Business logic modules
│   ├── scraper/          # Web scraping engine
│   ├── storegen/         # Static site generator
│   ├── pricing/          # Pricing rules and demand scoring
│   ├── dropship/         # Order routing to suppliers
│   ├── inventory/        # Inventory synchronisation
│   ├── payments/         # Payment gateway integrations
│   ├── config/           # Configuration loader
│   ├── logging/          # Logging wrapper
│   ├── models/           # SQLAlchemy and Pydantic models
│   ├── db/               # Database session setup and repositories
│   └── __init__.py
├── tests/                # Unit and integration tests
├── config.yaml           # YAML configuration file loaded by `core/config/settings.py`
├── main.py               # Application entry point
└── README.md / AGENTS.md # Project documentation and agent instructions

Development tasks
Codex should build the system step by step. Each numbered item below corresponds to a discrete task that Codex can run in isolation. After completing a task, commit the changes, verify that the associated tests pass, and move to the next task. If tests fail, fix the code and rerun them until they pass.
	1. Repository skeleton and configuration
		○ Create the folder structure shown above.
		○ Add an empty __init__.py to each package directory.
		○ Implement core/config/settings.py to load settings from config.yaml and expose helper functions such as get_db_url() and get_default_currency().
		○ Implement core/logging/logger.py to wrap Python’s logging module and provide a get_logger(name) function that returns a configured logger.
	2. Database setup and models
		○ In core/db/base.py, create an SQLAlchemy engine, a SessionLocal factory and a declarative Base class.
		○ Define SQLAlchemy models in core/models/ for Product, Variant, Image, Supplier, Order, OrderItem, Transaction, PriceRule and Store. Include appropriate column types and relationships (foreign keys). The Store model should encapsulate per‑store settings such as theme, price rules, payment provider and suppliers.
		○ Create corresponding Pydantic models for runtime data validation.
		○ Write a script core/db/init_db.py containing an init_db() function to create all tables. Ensure this function is called from main.py during startup.
	3. Repository classes
		○ Create a module core/db/repositories.py providing classes such as ProductRepository, OrderRepository, SupplierRepository, etc. Each repository should implement methods like get_by_id, get_all, create, update and any specialised queries (e.g. get_by_store(store_id) and get_pending_orders()).
		○ Write unit tests in tests/ to verify that these repositories perform CRUD operations correctly and respect store isolation.
	4. Scraper engine
		○ Implement core/scraper/request_manager.py with a RequestManager class that retrieves HTML, handles timeouts, retries, headers and optional proxies. Respect robots.txt and throttle requests to avoid blocking.
		○ Implement core/scraper/link_utils.py with functions such as normalize_url(href, base_url), is_same_domain(url, base_domain) and extract_links(html, base_url).
		○ Implement core/scraper/detectors.py containing heuristics to identify product pages (e.g. presence of a price tag or add‑to‑cart button) and optionally category pages.
		○ Implement core/scraper/extractors.py with functions like extract_product_data(html, url) that return raw product data (name, price, description, images, category, SKU).
		○ Implement core/scraper/orchestrator.py with a run_scrape(start_url, store_id) function that performs a breadth‑first crawl of all links on the domain, detects product pages, extracts data and saves normalised records to the database via the repository layer.
		○ Write tests with sample HTML pages to verify the detectors and extractors.
	5. Store generator
		○ Create a core/storegen/templates/ directory with Jinja2 templates for base.html, home.html, category.html and product.html. Keep the templates clean and avoid copying copyrighted text or logos from the scraped site.
		○ Implement core/storegen/theme_manager.py with a function to return the path of the selected theme. Support a default theme at first and allow easy extension for future themes.
		○ Implement core/storegen/builder.py with a function build_store(store_id, output_dir, theme_id="default"). The builder should read products for a specific store, group them into categories, render each template and write the resulting HTML files to output_dir.
		○ Implement core/storegen/exporter.py with functions to export static files or prepare data for deployment to Shopify/WooCommerce (in a later phase).
		○ Write tests to ensure that the store generator produces files containing the expected product names, prices and structure.
	6. Pricing engine
		○ Define rule classes in core/pricing/rules.py, including MarginRule (with fields such as minimum margin, maximum margin, category and price band) and DemandRule (weights for factors like base price and category).
		○ Implement core/pricing/demand_scoring.py with a compute_demand_score(product, rules) function that returns a float representing the predicted demand for a product based on the rule weights.
		○ Implement core/pricing/engine.py with a run_pricing(store_id) function that loads all products for a store, computes a demand score for each one, determines an appropriate margin multiplier, sets a new price field accordingly and saves it back to the database.
		○ Provide GUI controls (in a later task) to run pricing and preview changes.
	7. Dropshipping automation
		○ Extend the data model to include Order, OrderItem and Supplier tables. Add fields to record order status and tracking numbers.
		○ Create a core/dropship/adapters/base.py defining an abstract SupplierAdapter with methods place_order(order, order_item, supplier) and fetch_tracking(order, supplier).
		○ Add at least one concrete adapter in core/dropship/adapters/dummy_api.py that simulates placing an order with a supplier API for testing purposes. Real adapters for live suppliers can be implemented later.
		○ Implement core/dropship/router.py with a select_supplier(product_id) function that returns the appropriate supplier for a given product.
		○ Implement core/dropship/order_processor.py with a process_pending_orders() function that retrieves pending orders, iterates through items, calls the adapter to place the order, updates the order status and saves the tracking number.
		○ Schedule the order processor to run periodically using APScheduler (e.g. every few minutes) once integration is complete. Write tests to simulate order routing.
	8. Inventory synchronisation
		○ Implement core/inventory/sync_service.py with a sync_supplier_inventory(supplier_id) function that retrieves product availability and cost from the supplier (via API or scraping) and updates corresponding records in the database.
		○ After synchronising, the service should flag products whose supplier price changed significantly so that the pricing engine can be rerun.
		○ Use APScheduler to schedule periodic inventory synchronisation jobs. Write tests verifying that inventory and pricing are updated.
	9. Payment integration
		○ Introduce a core/payments package with a common interface in base.py exposing methods such as create_checkout_session(order), handle_webhook(payload) and refund(payment_id).
		○ Implement a StripeGateway class using Stripe’s Checkout Sessions API, which provides hosted or embedded payment pages that accept many local payment methods and require minimal client code. Accept API keys and configuration via config.yaml and never store raw card data.
		○ Implement a ShopifyGateway class using Shopify’s GraphQL Admin API, as all new apps must use GraphQL after April 1 2025. Authenticate requests with an X‑Shopify‑Access‑Token header and implement methods to push products, create checkout sessions and handle webhooks.
		○ Add a payment_provider column to the Store model so each store can choose between Stripe and Shopify. Extend main.py to instantiate the correct gateway per store.
		○ Use tokenised or virtual cards for supplier payments so that sensitive card data is never stored and compliance is simplified.
		○ Write tests simulating payment success, failure and refund scenarios.
	10. Multi‑store management
		○ Update models to link all core entities (products, price rules, orders, suppliers, payments) to a store_id foreign key.
		○ Implement a StoreManager service with methods to create, list, update and select stores. Ensure operations on one store do not affect others and that store‑specific settings (theme, payment provider, price rules) are respected.
		○ Modify repository and service functions to accept a store_id parameter. Update controllers to track the current store.
		○ Extend the GUI with a store selector and forms to manage store‑level settings.
	11. KPI instrumentation and metrics
		○ Instrument each module to record metrics such as:
			§ Number of products scraped, crawl depth and duration.
			§ Store generation time and number of pages generated.
			§ Pricing uplift (before/after margin difference).
			§ Order routing success and failure rates.
			§ Inventory synchronisation accuracy and frequency.
			§ Payment conversion rates and average checkout time.
		○ Implement a metrics collector (e.g. a simple Python service that aggregates counters and timing data). Provide APIs for the GUI to query metrics.
		○ Add a dashboard view in the GUI to display KPIs and logs in charts or tables. Write tests to verify metrics collection and retrieval.
	12. Machine‑learning pricing plugin (optional)
		○ Define a plugin interface in core/pricing/ml_plugin.py with fit(training_data) and predict(product) methods.
		○ Implement a baseline plugin using a gradient boosting algorithm (e.g. LightGBM) to predict demand and price elasticity from historical sales data. The plugin should output a recommended margin multiplier for each product.
		○ Integrate the plugin into the pricing engine so that, if configured and trained, it overrides the rule‑based margin; otherwise, fall back to the deterministic engine.
		○ Provide configuration options to enable or disable the ML plugin and to supply training data. Write tests using mock data to verify the plugin.
	13. Local GUI
		○ Choose a GUI framework (PyQt, Tkinter, Kivy or Mage). Implement app/gui.py with the main application window and navigation menu.
		○ Create views for the dashboard, scraper input, product list, pricing management, order management, store settings and metrics dashboard. Use controller classes to invoke core services without embedding business logic in the GUI.
		○ Provide inputs for domain URLs, run scraper, run pricing, select payment provider, generate store, manage orders and track metrics. Ensure the UI remains responsive during long operations by using worker threads or asynchronous calls.
	14. Main application & integration
		○ Write main.py to load configuration, initialise the database by calling init_db(), schedule background jobs for orders and inventory, instantiate the appropriate payment gateway for each store and launch the GUI.
		○ Implement command‑line arguments or a configuration screen to select environment (development vs production).
		○ Perform an end‑to‑end test: create a store, scrape a test site, run pricing, generate a storefront, simulate an order, process payment via the selected gateway and confirm supplier ordering and tracking.
	15. Compliance & legal considerations
		○ Enforce compliance with websites’ robots.txt files and terms of service in the scraper. Do not bypass anti‑bot mechanisms and limit request rates.
		○ Use only publicly available product data and paraphrase descriptions; never copy logos or proprietary branding.
		○ For payment processing, use tokenisation or virtual cards and rely on Stripe or Shopify to handle card data securely.
		○ Ensure multi‑store management isolates data so that personal or financial information does not leak between stores.
		○ Document any third‑party terms and ensure the project adheres to them (e.g. Shopify’s requirement to use GraphQL for new apps).
	16. Testing & quality assurance
		○ Write comprehensive unit tests for each module and integration tests for cross‑module flows.
		○ Use mocked API responses for suppliers and payment gateways to avoid external calls in tests.
		○ Implement continuous integration that runs tests and static code analysis on each change.
		○ Before release, conduct user acceptance tests to verify the GUI and end‑to‑end flows and perform security reviews.
Coding guidelines
	• Write clear, modular code. Separate concerns; avoid large, monolithic functions.
	• Follow PEP 8 style guidelines. Use descriptive names for variables, classes and functions.
	• Include docstrings and type hints for public functions and classes.
	• Write tests for new functionality. Use the tests/ directory and ensure that tests cover edge cases.
	• Never duplicate proprietary content. When replicating product descriptions, paraphrase them and avoid copying any copyrighted text or images. Do not copy logos or branding.
	• Respect websites’ robots.txt and terms of service. Implement rate limiting and user‑agent rotation in the scraper and do not attempt to bypass anti‑bot protections illegally.
	• Protect sensitive information. Do not store payment details or real customer data in the codebase. Use environment variables or secure payment gateways. When interacting with suppliers or customers, use tokenised or virtual card transactions and rely on third‑party processors to handle PCI compliance.
	• Adhere to safety policies. This project must not facilitate malware, malicious scraping, copyright infringement or any other illegal or unethical activity.
Allowed commands and resources
The following commands are permitted in Codex tasks:
	• python <script> – run Python code.
	• pytest -q – run all tests quietly.
	• pip install <package> – install necessary Python packages (use sparingly; verify they are safe and needed).
	• Standard shell commands such as ls, pwd to navigate the file system.
	• Running scripts in scripts/ (if created later) for setup or data seeding.
Internet access is disabled by default in Codex tasks for security reasons. You should not attempt to fetch external resources unless explicitly enabled via a project configuration. When external data is required (e.g. to fetch pricing info), provide a mocked response in tests or use a test API.
What to do when uncertain
Codex should halt and ask for clarification in its UI when it encounters ambiguity that prevents progress (e.g. lacking information on a supplier’s API). When tests fail, fix the implementation before moving on. If there is a disagreement between these instructions and an individual task prompt, prefer these instructions unless the task clearly supersedes them.<img width="644" height="5037" alt="image" src="https://github.com/user-attachments/assets/dfc3d8ad-ba7b-4bfb-94a8-62ec29318e9d" />

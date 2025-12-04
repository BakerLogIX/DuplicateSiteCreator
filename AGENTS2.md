Duplicate Site Creator – Supplemental Agent Notes

This file captures gaps from the original AGENTS instructions plus a concrete deployment plan for Codex to follow.

Missed or under-specified items
- Scraper engine (Task 4): Implement request_manager.py (timeouts, retries, robots.txt respect, throttle), link_utils.py (normalize_url, is_same_domain, extract_links), detectors.py (heuristics for product/category pages), extractors.py (name, price, description, images, category, SKU), orchestrator.py (BFS crawl constrained to domain, detect product pages, persist via repositories), and tests with sample HTML.
- Payments (Task 9): Build core/payments/base.py with gateway interface; StripeGateway using Checkout Sessions (no raw card data) and ShopifyGateway using GraphQL Admin API with X-Shopify-Access-Token. Store.payment_provider should select gateway in main/bootstrap paths. Add tests for success/failure/refund.
- Multi-store completeness (Task 10): Ensure all services/repositories enforce store_id isolation, add StoreManager-driven selection in controllers/GUI, and store-specific settings (theme, payment provider, price rules). Provide forms in Settings view.
- Metrics/KPIs (Task 11): Implement metrics collector service with counters/timers (scrape depth/time, products scraped, pricing uplift, pages generated, order routing success/failure, inventory sync accuracy/frequency, payment conversion). Expose query APIs and add GUI dashboard view.
- Compliance (Task 15): Document robots.txt adherence, throttling, paraphrasing of scraped text, and prohibition on logos/branding. Ensure scheduler jobs and scraper respect rate limits.
- QA/CI (Task 16): Add broader unit/integration coverage (mocked external calls), and a CI workflow to run pytest and static checks.

Deployment plan for Codex
1) Scraper implementation: Add the full scraper module (request manager, link utils, detectors, extractors, orchestrator) plus tests using bundled HTML fixtures. Verify pytest passes.
2) Payment gateways: Implement payment interface and Stripe/Shopify gateways with config-driven credentials and mocks for tests. Wire gateway selection in main/bootstrap and expand tests to cover charge/refund flows.
3) Multi-store hardening: Audit services/controllers to ensure store_id isolation and allow store selection/settings in GUI. Add tests for isolation.
4) Metrics layer: Build a lightweight metrics collector and instrument scraper, storegen, pricing, dropship, inventory, and payments. Expose GUI dashboard. Add tests for metric accumulation/query.
5) Compliance and QA: Add a compliance note/doc, enforce rate limits/robots checks, and introduce CI (GitHub Actions) running pytest (and linters if added).

Operational notes
- Keep ASCII-only content, follow PEP 8, add concise docstrings/type hints, and prefer unit tests with mocked external calls.
- Respect sandbox/no-network defaults; mock APIs for suppliers/payments/scraper tests.

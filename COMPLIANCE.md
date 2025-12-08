# Compliance & Safety Notes

This project is designed to respect legal and ethical boundaries while scraping and automating storefronts.

- **Robots.txt and rate limits:** The scraper respects `robots.txt` by default and throttles requests per domain (`RequestManager` uses a configurable minimum interval). Do not disable these safeguards when targeting third-party sites.
- **Public data only:** Scraping must be limited to publicly available product data. Do not bypass anti-bot measures or access gated content.
- **Paraphrased content:** When generating storefronts, avoid copying proprietary branding or descriptions verbatim. Paraphrase text and never copy logos.
- **Payment security:** Payment processing relies on Stripe or Shopify tokenisation. Raw card data must never be stored or transmitted by this application.
- **Multi-store isolation:** Each store’s data is isolated by `store_id`; avoid cross-store data leakage in new code.
- **Supplier interactions:** Use test credentials or sandbox endpoints for supplier APIs. Mock external calls in tests; never hardcode real secrets.
- **Logging:** Keep logs free of sensitive customer or payment details.

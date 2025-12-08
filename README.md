# DuplicateSiteCreator
Application that duplicates sites for small merchants.

## Quick start
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `pytest -q`
- Launch app: `python main.py`

## Compliance & safety
See `COMPLIANCE.md` for the scraping and payment safety rules this project follows (robots.txt, rate limits, paraphrasing, tokenised payments, and store isolation).

## CI
GitHub Actions workflow (`.github/workflows/ci.yml`) runs pytest on pushes and pull requests to keep the test suite green.

"""Scraper package exports."""
from core.scraper.detectors import detect_category_page, detect_product_page
from core.scraper.extractors import extract_product_data
from core.scraper.orchestrator import run_scrape
from core.scraper.request_manager import RequestManager

__all__ = [
    "detect_category_page",
    "detect_product_page",
    "extract_product_data",
    "RequestManager",
    "run_scrape",
]

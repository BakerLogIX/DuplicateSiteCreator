"""Inventory synchronisation service."""
from core.logging.logger import get_logger

logger = get_logger(__name__)


def sync_supplier_inventory(supplier_id: int) -> None:
    logger.info("Synchronising inventory for supplier %s", supplier_id)
    # Placeholder: real implementation would fetch supplier data and update products

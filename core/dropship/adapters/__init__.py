"""Supplier adapter exports."""
from core.dropship.adapters.base import SupplierAdapter
from core.dropship.adapters.dummy_api import DummySupplierAdapter

__all__ = ["SupplierAdapter", "DummySupplierAdapter"]

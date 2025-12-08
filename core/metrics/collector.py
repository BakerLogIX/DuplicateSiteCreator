"""Thread-safe in-memory metrics collector for counters and observations."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
from time import perf_counter
from typing import DefaultDict, Dict, List, Optional
from collections import defaultdict


@dataclass
class MeasurementStats:
    """Aggregate statistics for a metric."""

    count: int
    avg: float
    minimum: float
    maximum: float


class MetricsCollector:
    """In-memory collector storing counters and observed values per store."""

    def __init__(self) -> None:
        self._counters: DefaultDict[str, DefaultDict[Optional[int], float]] = defaultdict(
            lambda: defaultdict(float)
        )
        self._measurements: DefaultDict[str, DefaultDict[Optional[int], List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._lock = Lock()

    def increment(self, name: str, amount: float = 1, *, store_id: Optional[int] = None) -> None:
        """Increase a counter by the provided amount."""

        with self._lock:
            self._counters[name][store_id] += amount

    def observe(self, name: str, value: float, *, store_id: Optional[int] = None) -> None:
        """Record a numeric observation for later aggregation."""

        with self._lock:
            self._measurements[name][store_id].append(float(value))

    @contextmanager
    def timer(self, name: str, *, store_id: Optional[int] = None):
        """Context manager that records elapsed seconds for a block of code."""

        start = perf_counter()
        try:
            yield
        finally:
            duration = perf_counter() - start
            self.observe(name, duration, store_id=store_id)

    def get_snapshot(self, store_id: Optional[int] = None) -> Dict[str, Dict[str, object]]:
        """Return aggregated metrics for a specific store."""

        with self._lock:
            counters = {name: store_map.get(store_id, 0) for name, store_map in self._counters.items()}

            measurements: Dict[str, MeasurementStats] = {}
            for name, store_map in self._measurements.items():
                values = list(store_map.get(store_id, []))
                if not values:
                    measurements[name] = MeasurementStats(count=0, avg=0.0, minimum=0.0, maximum=0.0)
                    continue
                count = len(values)
                measurements[name] = MeasurementStats(
                    count=count,
                    avg=sum(values) / count,
                    minimum=min(values),
                    maximum=max(values),
                )

            return {
                "counters": counters,
                "measurements": measurements,
            }

    def reset(self) -> None:
        """Clear all recorded metrics (useful for tests)."""

        with self._lock:
            self._counters.clear()
            self._measurements.clear()


_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    """Return the process-wide metrics collector."""

    return _collector


__all__ = ["MetricsCollector", "MeasurementStats", "get_collector"]

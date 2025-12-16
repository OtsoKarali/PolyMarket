"""Observability: structured logging and metrics."""

import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(log_level="INFO"),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


class Metrics:
    """Simple metrics counter for ingestion tracking."""

    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}

    def increment(self, metric: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        key = self._format_key(metric, tags)
        self.counters[key] = self.counters.get(key, 0) + value
        logger.info("metric.increment", metric=metric, value=value, tags=tags, total=self.counters[key])

    def gauge(self, metric: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        key = self._format_key(metric, tags)
        self.gauges[key] = value
        logger.info("metric.gauge", metric=metric, value=value, tags=tags)

    def get_counter(self, metric: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        key = self._format_key(metric, tags)
        return self.counters.get(key, 0)

    def _format_key(self, metric: str, tags: Optional[Dict[str, str]]) -> str:
        """Format metric key with tags."""
        if not tags:
            return metric
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric}[{tag_str}]"

    def reset(self):
        """Reset all metrics (useful for testing)."""
        self.counters.clear()
        self.gauges.clear()


# Global metrics instance
metrics = Metrics()


@contextmanager
def log_duration(operation: str, **context: Any):
    """Context manager to log operation duration."""
    start = time.time()
    logger.info(f"{operation}.start", **context)
    try:
        yield
        duration = time.time() - start
        logger.info(f"{operation}.complete", duration_seconds=duration, **context)
        metrics.gauge(f"{operation}.duration", duration, context)
    except Exception as e:
        duration = time.time() - start
        logger.error(
            f"{operation}.error",
            error=str(e),
            error_type=type(e).__name__,
            duration_seconds=duration,
            **context,
        )
        metrics.increment(f"{operation}.errors", tags=context)
        raise


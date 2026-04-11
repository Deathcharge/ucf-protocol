"""
Advanced Features for UCF Protocol - Production-Ready Patterns

Provides enterprise-grade features for caching, monitoring, resilience,
and performance optimization.

Features:
- CacheManager: Intelligent caching with multiple eviction policies
- MonitoringSystem: Performance metrics collection and analysis
- RetryPolicy: Exponential backoff retry mechanism
- CircuitBreaker: Fault tolerance pattern
- RateLimiter: Token bucket rate limiting
- HealthChecker: System health monitoring
- Utility Functions: Timeout handling and measurement
"""

import time
import logging
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, List, Optional, Callable
from collections import OrderedDict
from enum import Enum
from functools import wraps
import threading
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================================
# CACHE MANAGER
# ============================================================================

class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "least_recently_used"
    LFU = "least_frequently_used"
    FIFO = "first_in_first_out"


class CacheManager:
    """Intelligent cache with configurable eviction policies."""
    
    def __init__(self, max_size: int = 1000, policy: EvictionPolicy = EvictionPolicy.LRU):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of items in cache
            policy: Eviction policy (LRU, LFU, FIFO)
        """
        self.max_size = max_size
        self.policy = policy
        self.cache: Dict[str, Any] = {}
        self.access_count: Dict[str, int] = {}
        self.access_time: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key in self.cache:
                self.access_time[key] = time.time()
                self.access_count[key] = self.access_count.get(key, 0) + 1
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self.lock:
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
            
            self.cache[key] = value
            self.access_time[key] = time.time()
            self.access_count[key] = 1
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        with self.lock:
            self.cache.pop(key, None)
            self.access_count.pop(key, None)
            self.access_time.pop(key, None)
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self.lock:
            self.cache.clear()
            self.access_count.clear()
            self.access_time.clear()
    
    def _evict(self) -> None:
        """Evict item based on policy."""
        if not self.cache:
            return
        
        if self.policy == EvictionPolicy.LRU:
            key_to_evict = min(self.access_time, key=self.access_time.get)
        elif self.policy == EvictionPolicy.LFU:
            key_to_evict = min(self.access_count, key=self.access_count.get)
        elif self.policy == EvictionPolicy.FIFO:
            key_to_evict = next(iter(self.cache))
        else:
            key_to_evict = next(iter(self.cache))
        
        self.delete(key_to_evict)
        logger.debug(f"Evicted cache key: {key_to_evict}")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'policy': self.policy.value,
            'total_accesses': sum(self.access_count.values()),
        }


# ============================================================================
# MONITORING SYSTEM
# ============================================================================

@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class MonitoringSystem:
    """Performance metrics collection and analysis."""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize monitoring system.
        
        Args:
            window_size: Number of metrics to keep in memory
        """
        self.window_size = window_size
        self.metrics: Dict[str, List[Metric]] = {}
        self.lock = threading.RLock()
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric."""
        with self.lock:
            metric = Metric(name=name, value=value, tags=tags or {})
            
            if name not in self.metrics:
                self.metrics[name] = []
            
            self.metrics[name].append(metric)
            
            # Keep only recent metrics
            if len(self.metrics[name]) > self.window_size:
                self.metrics[name] = self.metrics[name][-self.window_size:]
    
    def get_stats(self, name: str) -> Optional[Dict[str, float]]:
        """Get statistics for a metric."""
        with self.lock:
            if name not in self.metrics or not self.metrics[name]:
                return None
            
            values = [m.value for m in self.metrics[name]]
            
            return {
                'count': len(values),
                'sum': sum(values),
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'latest': values[-1],
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all metrics."""
        return {name: self.get_stats(name) for name in self.metrics}
    
    def clear(self) -> None:
        """Clear all metrics."""
        with self.lock:
            self.metrics.clear()


# ============================================================================
# RETRY POLICY
# ============================================================================

class RetryPolicy:
    """Exponential backoff retry mechanism."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Initialize retry policy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_attempts} attempts failed")
        
        raise last_exception
    
    def decorator(self, func: Callable) -> Callable:
        """Decorator for automatic retry."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)
        return wrapper


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Fault tolerance pattern for graceful degradation."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.lock = threading.RLock()
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise RuntimeError("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise
    
    def _on_success(self) -> None:
        """Handle successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker CLOSED")
    
    def _on_failure(self) -> None:
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if self.last_failure_time is None:
            return False
        
        return time.time() - self.last_failure_time >= self.timeout
    
    def get_state(self) -> str:
        """Get current circuit state."""
        return self.state.value


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Token bucket rate limiting algorithm."""
    
    def __init__(self, rate: float, capacity: float):
        """
        Initialize rate limiter.
        
        Args:
            rate: Tokens per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.RLock()
    
    def acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens."""
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
    
    def get_available(self) -> float:
        """Get available tokens."""
        with self.lock:
            self._refill()
            return self.tokens


# ============================================================================
# HEALTH CHECKER
# ============================================================================

@dataclass
class HealthStatus:
    """Health check result."""
    healthy: bool
    checks: Dict[str, bool]
    timestamp: float = field(default_factory=time.time)
    message: str = ""


class HealthChecker:
    """System health monitoring."""
    
    def __init__(self):
        """Initialize health checker."""
        self.checks: Dict[str, Callable] = {}
        self.lock = threading.RLock()
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """Register a health check function."""
        with self.lock:
            self.checks[name] = check_func
    
    def check(self) -> HealthStatus:
        """Run all health checks."""
        with self.lock:
            results = {}
            
            for name, check_func in self.checks.items():
                try:
                    results[name] = check_func()
                except Exception as e:
                    logger.error(f"Health check '{name}' failed: {e}")
                    results[name] = False
            
            healthy = all(results.values())
            
            return HealthStatus(
                healthy=healthy,
                checks=results,
                message="All checks passed" if healthy else "Some checks failed",
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get health status as dictionary."""
        status = self.check()
        return {
            'healthy': status.healthy,
            'checks': status.checks,
            'timestamp': status.timestamp,
            'message': status.message,
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.time() - start
            logger.debug(f"{func.__name__} took {elapsed:.4f}s")
    return wrapper


def with_timeout(timeout_seconds: float) -> Callable:
    """Decorator to add timeout to function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
            
            # Set signal handler
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
        
        return wrapper
    return decorator


def retry_on_exception(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """Decorator for automatic retry on exception."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            policy = RetryPolicy(max_attempts=max_attempts, base_delay=delay)
            return policy.execute(func, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit(rate: float, capacity: float) -> Callable:
    """Decorator for rate limiting."""
    limiter = RateLimiter(rate=rate, capacity=capacity)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.acquire():
                raise RuntimeError("Rate limit exceeded")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# PERFORMANCE MEASUREMENT
# ============================================================================

class PerformanceMonitor:
    """Monitor and report performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.monitoring = MonitoringSystem()
        self.cache = CacheManager()
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter(rate=100.0, capacity=100.0)
        self.health_checker = HealthChecker()
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'metrics': self.monitoring.get_all_stats(),
            'cache': self.cache.stats(),
            'circuit_breaker': self.circuit_breaker.get_state(),
            'rate_limiter': {
                'available_tokens': self.rate_limiter.get_available(),
            },
            'health': self.health_checker.get_status(),
        }


# ============================================================================
# INITIALIZATION
# ============================================================================

# Global instances
_cache_manager = CacheManager()
_monitoring_system = MonitoringSystem()
_performance_monitor = PerformanceMonitor()


def get_cache() -> CacheManager:
    """Get global cache manager instance."""
    return _cache_manager


def get_monitoring() -> MonitoringSystem:
    """Get global monitoring system instance."""
    return _monitoring_system


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    return _performance_monitor

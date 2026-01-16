"""
Circuit Breaker Implementation
Prevents cascading failures in service-to-service calls.
"""

import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
            return self._state
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to attempt recovery."""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout
    
    def record_success(self):
        """Record successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED (recovered)")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    def record_failure(self):
        """Record failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (still failing)")
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.failure_threshold:
                logger.warning(f"Circuit {self.name}: CLOSED -> OPEN (threshold reached)")
                self._state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """Check if request can proceed."""
        return self.state != CircuitState.OPEN
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        
        return wrapper


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is rejected."""
    pass


# Pre-configured circuit breakers for services
CIRCUIT_BREAKERS = {
    "feature_service": CircuitBreaker(
        name="feature_service",
        failure_threshold=5,
        recovery_timeout=30.0
    ),
    "inference_service": CircuitBreaker(
        name="inference_service",
        failure_threshold=3,
        recovery_timeout=60.0
    ),
    "decision_engine": CircuitBreaker(
        name="decision_engine",
        failure_threshold=5,
        recovery_timeout=30.0
    ),
    "llm_service": CircuitBreaker(
        name="llm_service",
        failure_threshold=2,
        recovery_timeout=120.0  # Longer for LLM
    ),
}


def get_circuit(name: str) -> CircuitBreaker:
    """Get circuit breaker by name."""
    return CIRCUIT_BREAKERS.get(name, CircuitBreaker(name=name))

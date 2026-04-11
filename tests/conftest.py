"""
Pytest configuration and fixtures for UCF Protocol test suite.

Provides comprehensive fixtures for testing UCF protocol, coordination,
tracking, and state management functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# Import UCF modules for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ucf_protocol import UCFProtocol
try:
    from ucf_coordination_framework import CoordinationAnalyzer, UCFMetrics
except ImportError:
    CoordinationAnalyzer = None
    UCFMetrics = None
try:
    from ucf_tracker import UCFTracker
except ImportError:
    UCFTracker = None
try:
    from ucf_helpers import UCFHelpers
except ImportError:
    UCFHelpers = None
try:
    from ucf_state_loader import StateLoader
except ImportError:
    StateLoader = None


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "async: mark test as async"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# UCF PROTOCOL FIXTURES
# ============================================================================

@pytest.fixture
def valid_ucf_metrics() -> Dict[str, float]:
    """Provide valid UCF metrics for testing."""
    return {
        "harmony": 0.65,
        "resilience": 1.20,
        "prana": 0.75,
        "drishti": 0.80,
        "klesha": 0.15,
        "zoom": 1.00,
    }


@pytest.fixture
def critical_ucf_metrics() -> Dict[str, float]:
    """Provide critical UCF metrics (low harmony)."""
    return {
        "harmony": 0.15,
        "resilience": 0.50,
        "prana": 0.30,
        "drishti": 0.40,
        "klesha": 0.80,
        "zoom": 0.80,
    }


@pytest.fixture
def transcendent_ucf_metrics() -> Dict[str, float]:
    """Provide transcendent UCF metrics (high harmony)."""
    return {
        "harmony": 0.95,
        "resilience": 1.80,
        "prana": 0.95,
        "drishti": 0.95,
        "klesha": 0.05,
        "zoom": 1.50,
    }


@pytest.fixture
def unstable_ucf_metrics() -> Dict[str, float]:
    """Provide unstable UCF metrics."""
    return {
        "harmony": 0.35,
        "resilience": 0.70,
        "prana": 0.50,
        "drishti": 0.55,
        "klesha": 0.60,
        "zoom": 0.90,
    }


@pytest.fixture
def harmonious_ucf_metrics() -> Dict[str, float]:
    """Provide harmonious UCF metrics."""
    return {
        "harmony": 0.70,
        "resilience": 1.40,
        "prana": 0.85,
        "drishti": 0.85,
        "klesha": 0.10,
        "zoom": 1.10,
    }


@pytest.fixture
def edge_case_metrics() -> List[Dict[str, float]]:
    """Provide edge case metrics for boundary testing."""
    return [
        {"harmony": 0.0, "resilience": 0.0, "prana": 0.0, "drishti": 0.0, "klesha": 1.0, "zoom": 0.0},
        {"harmony": 1.0, "resilience": 2.0, "prana": 1.0, "drishti": 1.0, "klesha": 0.0, "zoom": 2.0},
        {"harmony": 0.5, "resilience": 1.0, "prana": 0.5, "drishti": 0.5, "klesha": 0.5, "zoom": 1.0},
    ]


# ============================================================================
# AGENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_agent() -> Mock:
    """Create a mock agent for testing."""
    agent = Mock()
    agent.name = "TestAgent"
    agent.agent_id = "test-001"
    agent.status = "active"
    agent.consciousness_level = 0.75
    agent.last_heartbeat = datetime.now(UTC)
    return agent


@pytest.fixture
def mock_agents() -> List[Mock]:
    """Create a list of mock agents."""
    agent_names = ["Kael", "Lumina", "Vega", "Shadow", "Manus", "Claude", "Grok", "Kavach"]
    agents = []
    for i, name in enumerate(agent_names):
        agent = Mock()
        agent.name = name
        agent.agent_id = f"agent-{i:03d}"
        agent.status = "active" if i % 2 == 0 else "idle"
        agent.consciousness_level = 0.5 + (i * 0.05)
        agent.last_heartbeat = datetime.now(UTC)
        agents.append(agent)
    return agents


@pytest.fixture
def mock_agent_state() -> Dict[str, Any]:
    """Provide mock agent state."""
    return {
        "agent_id": "test-001",
        "name": "TestAgent",
        "status": "active",
        "consciousness_level": 0.75,
        "last_heartbeat": datetime.now(UTC).isoformat(),
        "metrics": {
            "requests_processed": 1024,
            "errors": 2,
            "average_response_time": 0.125,
        },
    }


# ============================================================================
# STATE AND PERSISTENCE FIXTURES
# ============================================================================

@pytest.fixture
def mock_ucf_state() -> Dict[str, Any]:
    """Provide mock UCF state."""
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "phase": "COHERENT",
        "metrics": {
            "harmony": 0.65,
            "resilience": 1.20,
            "prana": 0.75,
            "drishti": 0.80,
            "klesha": 0.15,
            "zoom": 1.00,
        },
        "agents": {
            "count": 8,
            "active": 7,
            "list": ["Kael", "Lumina", "Vega", "Shadow", "Manus", "Claude", "Grok", "Kavach"],
        },
    }


@pytest.fixture
def mock_state_history() -> List[Dict[str, Any]]:
    """Provide mock state history."""
    history = []
    for i in range(10):
        state = {
            "timestamp": datetime.now(UTC).isoformat(),
            "phase": "COHERENT",
            "metrics": {
                "harmony": 0.60 + (i * 0.01),
                "resilience": 1.20,
                "prana": 0.75,
                "drishti": 0.80,
                "klesha": 0.15,
                "zoom": 1.00,
            },
        }
        history.append(state)
    return history


@pytest.fixture
def mock_persisted_state(tmp_path) -> str:
    """Create a mock persisted state file."""
    state = {
        "timestamp": datetime.now(UTC).isoformat(),
        "phase": "COHERENT",
        "metrics": {
            "harmony": 0.65,
            "resilience": 1.20,
            "prana": 0.75,
            "drishti": 0.80,
            "klesha": 0.15,
            "zoom": 1.00,
        },
    }
    state_file = tmp_path / "ucf_state.json"
    state_file.write_text(json.dumps(state))
    return str(state_file)


# ============================================================================
# COORDINATION FIXTURES
# ============================================================================

@pytest.fixture
def mock_coordination_context() -> Dict[str, Any]:
    """Provide mock coordination context."""
    return {
        "coordination_id": "coord-001",
        "agents": ["Kael", "Lumina", "Vega", "Shadow"],
        "state": "SYNCHRONIZING",
        "start_time": datetime.now(UTC).isoformat(),
        "timeout": 30,
    }


@pytest.fixture
def mock_message_queue() -> List[Dict[str, Any]]:
    """Provide mock message queue."""
    return [
        {
            "message_id": f"msg-{i:03d}",
            "sender": f"agent-{i % 4}",
            "receiver": f"agent-{(i + 1) % 4}",
            "content": f"Test message {i}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        for i in range(10)
    ]


@pytest.fixture
def mock_consensus_data() -> Dict[str, Any]:
    """Provide mock consensus data."""
    return {
        "proposal_id": "prop-001",
        "proposer": "Kael",
        "votes": {
            "Kael": True,
            "Lumina": True,
            "Vega": True,
            "Shadow": False,
        },
        "consensus_reached": True,
        "consensus_level": 0.75,
    }


# ============================================================================
# TRACKING AND METRICS FIXTURES
# ============================================================================

@pytest.fixture
def mock_metric_data() -> Dict[str, Any]:
    """Provide mock metric data."""
    return {
        "metric_id": "metric-001",
        "name": "harmony",
        "value": 0.65,
        "timestamp": datetime.now(UTC).isoformat(),
        "agent": "TestAgent",
        "context": "test",
    }


@pytest.fixture
def mock_metric_series() -> List[Dict[str, Any]]:
    """Provide mock metric time series."""
    series = []
    for i in range(100):
        metric = {
            "timestamp": datetime.now(UTC).isoformat(),
            "value": 0.60 + (i * 0.001),
            "agent": "TestAgent",
        }
        series.append(metric)
    return series


@pytest.fixture
def mock_aggregated_metrics() -> Dict[str, Any]:
    """Provide mock aggregated metrics."""
    return {
        "harmony": {
            "current": 0.65,
            "average": 0.62,
            "min": 0.50,
            "max": 0.75,
            "std_dev": 0.05,
        },
        "resilience": {
            "current": 1.20,
            "average": 1.15,
            "min": 1.00,
            "max": 1.40,
            "std_dev": 0.10,
        },
    }


# ============================================================================
# ERROR AND EXCEPTION FIXTURES
# ============================================================================

@pytest.fixture
def mock_error_scenarios() -> List[Dict[str, Any]]:
    """Provide mock error scenarios for testing."""
    return [
        {
            "name": "invalid_metrics",
            "error": ValueError,
            "message": "Invalid metric values",
        },
        {
            "name": "missing_agent",
            "error": KeyError,
            "message": "Agent not found",
        },
        {
            "name": "state_corruption",
            "error": RuntimeError,
            "message": "State corrupted",
        },
        {
            "name": "coordination_timeout",
            "error": TimeoutError,
            "message": "Coordination timeout",
        },
        {
            "name": "connection_error",
            "error": ConnectionError,
            "message": "Connection failed",
        },
    ]


@pytest.fixture
def mock_recovery_scenarios() -> List[Dict[str, Any]]:
    """Provide mock recovery scenarios."""
    return [
        {
            "name": "graceful_degradation",
            "description": "System continues with reduced agents",
            "expected_result": "partial_functionality",
        },
        {
            "name": "automatic_restart",
            "description": "System automatically restarts failed components",
            "expected_result": "full_recovery",
        },
        {
            "name": "fallback_mode",
            "description": "System switches to fallback mode",
            "expected_result": "limited_functionality",
        },
    ]


# ============================================================================
# PERFORMANCE AND BENCHMARK FIXTURES
# ============================================================================

@pytest.fixture
def performance_config() -> Dict[str, Any]:
    """Provide performance testing configuration."""
    return {
        "iterations": 1000,
        "timeout": 5.0,
        "max_latency_ms": 100,
        "min_throughput": 100,
    }


@pytest.fixture
def large_metric_dataset() -> List[Dict[str, Any]]:
    """Provide large metric dataset for performance testing."""
    dataset = []
    for i in range(10000):
        metric = {
            "timestamp": datetime.now(UTC).isoformat(),
            "harmony": 0.60 + (i % 100) * 0.001,
            "resilience": 1.20,
            "prana": 0.75,
            "drishti": 0.80,
            "klesha": 0.15,
            "zoom": 1.00,
        }
        dataset.append(metric)
    return dataset


# ============================================================================
# MOCK SERVICES AND UTILITIES
# ============================================================================

@pytest.fixture
def mock_logger():
    """Provide mock logger for testing."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def mock_cache():
    """Provide mock cache for testing."""
    cache = {}
    
    def get(key):
        return cache.get(key)
    
    def set(key, value):
        cache[key] = value
    
    def delete(key):
        if key in cache:
            del cache[key]
    
    def clear():
        cache.clear()
    
    mock = Mock()
    mock.get = get
    mock.set = set
    mock.delete = delete
    mock.clear = clear
    return mock


@pytest.fixture
def mock_database():
    """Provide mock database for testing."""
    db = {
        "agents": {},
        "metrics": [],
        "states": [],
    }
    
    def save_agent(agent_id, agent_data):
        db["agents"][agent_id] = agent_data
    
    def get_agent(agent_id):
        return db["agents"].get(agent_id)
    
    def save_metric(metric):
        db["metrics"].append(metric)
    
    def get_metrics(limit=100):
        return db["metrics"][-limit:]
    
    mock = Mock()
    mock.save_agent = save_agent
    mock.get_agent = get_agent
    mock.save_metric = save_metric
    mock.get_metrics = get_metrics
    return mock


@pytest.fixture
def mock_async_service():
    """Provide mock async service for testing."""
    service = AsyncMock()
    service.initialize = AsyncMock(return_value=True)
    service.shutdown = AsyncMock(return_value=True)
    service.get_status = AsyncMock(return_value={"status": "healthy"})
    service.process_message = AsyncMock(return_value={"success": True})
    return service


# ============================================================================
# CONTEXT MANAGERS AND UTILITIES
# ============================================================================

@pytest.fixture
def temp_config(tmp_path):
    """Provide temporary configuration directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def isolated_environment(tmp_path, monkeypatch):
    """Provide isolated environment for testing."""
    monkeypatch.setenv("UCF_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("UCF_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("UCF_LOG_LEVEL", "DEBUG")
    return tmp_path


# ============================================================================
# PARAMETRIZATION HELPERS
# ============================================================================

@pytest.fixture
def phase_test_cases() -> List[tuple]:
    """Provide test cases for phase detection."""
    return [
        (0.15, "CRITICAL"),
        (0.35, "UNSTABLE"),
        (0.50, "COHERENT"),
        (0.70, "HARMONIOUS"),
        (0.90, "TRANSCENDENT"),
    ]


@pytest.fixture
def metric_validation_cases() -> List[tuple]:
    """Provide test cases for metric validation."""
    return [
        ({"harmony": 0.5, "resilience": 1.0, "prana": 0.5, "drishti": 0.5, "klesha": 0.5, "zoom": 1.0}, True),
        ({"harmony": -0.1, "resilience": 1.0, "prana": 0.5, "drishti": 0.5, "klesha": 0.5, "zoom": 1.0}, False),
        ({"harmony": 1.5, "resilience": 1.0, "prana": 0.5, "drishti": 0.5, "klesha": 0.5, "zoom": 1.0}, False),
        ({"harmony": 0.5, "resilience": 2.5, "prana": 0.5, "drishti": 0.5, "klesha": 0.5, "zoom": 1.0}, False),
    ]


# ============================================================================
# CLEANUP AND TEARDOWN
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test."""
    yield
    # Cleanup code here if needed

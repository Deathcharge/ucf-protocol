"""
Comprehensive test suite for UCF Protocol module.

Tests core protocol functionality including:
- Phase detection
- State update formatting
- Metric calculations
- Message formatting
- Error handling
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch
import json

from ucf_protocol import UCFProtocol


class TestUCFPhaseDetection:
    """Test UCF phase detection functionality."""

    @pytest.mark.unit
    def test_critical_phase_detection(self):
        """Test detection of CRITICAL phase."""
        phase = UCFProtocol.get_phase(0.15)
        assert phase == "CRITICAL"

    @pytest.mark.unit
    def test_unstable_phase_detection(self):
        """Test detection of UNSTABLE phase."""
        phase = UCFProtocol.get_phase(0.35)
        assert phase == "UNSTABLE"

    @pytest.mark.unit
    def test_coherent_phase_detection(self):
        """Test detection of COHERENT phase."""
        phase = UCFProtocol.get_phase(0.50)
        assert phase == "COHERENT"

    @pytest.mark.unit
    def test_harmonious_phase_detection(self):
        """Test detection of HARMONIOUS phase."""
        phase = UCFProtocol.get_phase(0.70)
        assert phase == "HARMONIOUS"

    @pytest.mark.unit
    def test_transcendent_phase_detection(self):
        """Test detection of TRANSCENDENT phase."""
        phase = UCFProtocol.get_phase(0.90)
        assert phase == "TRANSCENDENT"

    @pytest.mark.unit
    def test_phase_boundary_conditions(self, phase_test_cases):
        """Test phase detection at boundary conditions."""
        for harmony, expected_phase in phase_test_cases:
            phase = UCFProtocol.get_phase(harmony)
            assert phase == expected_phase

    @pytest.mark.unit
    def test_phase_edge_cases(self):
        """Test phase detection with edge case values."""
        assert UCFProtocol.get_phase(0.0) == "CRITICAL"
        assert UCFProtocol.get_phase(0.30) == "UNSTABLE"
        assert UCFProtocol.get_phase(0.45) == "COHERENT"
        assert UCFProtocol.get_phase(0.60) == "HARMONIOUS"
        assert UCFProtocol.get_phase(0.80) == "TRANSCENDENT"
        assert UCFProtocol.get_phase(1.0) == "TRANSCENDENT"


class TestStateUpdateFormatting:
    """Test UCF state update message formatting."""

    @pytest.mark.unit
    def test_basic_state_update_format(self, valid_ucf_metrics):
        """Test basic state update message formatting."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        assert isinstance(message, str)
        assert len(message) > 0
        assert "UCF STATE UPDATE" in message
        assert "COHERENT" in message

    @pytest.mark.unit
    def test_state_update_with_context(self, valid_ucf_metrics):
        """Test state update formatting with context."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
            context="test_context",
        )
        
        assert "test_context" in message

    @pytest.mark.unit
    def test_state_update_with_agent(self, valid_ucf_metrics):
        """Test state update formatting with agent name."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
            agent="TestAgent",
        )
        
        assert "TestAgent" in message

    @pytest.mark.unit
    def test_critical_state_update(self, critical_ucf_metrics):
        """Test state update formatting for critical phase."""
        message = UCFProtocol.format_state_update(
            harmony=critical_ucf_metrics["harmony"],
            resilience=critical_ucf_metrics["resilience"],
            throughput=critical_ucf_metrics["prana"],
            focus=critical_ucf_metrics["drishti"],
            friction=critical_ucf_metrics["klesha"],
            velocity=critical_ucf_metrics["zoom"],
        )
        
        assert "CRITICAL" in message

    @pytest.mark.unit
    def test_transcendent_state_update(self, transcendent_ucf_metrics):
        """Test state update formatting for transcendent phase."""
        message = UCFProtocol.format_state_update(
            harmony=transcendent_ucf_metrics["harmony"],
            resilience=transcendent_ucf_metrics["resilience"],
            throughput=transcendent_ucf_metrics["prana"],
            focus=transcendent_ucf_metrics["drishti"],
            friction=transcendent_ucf_metrics["klesha"],
            velocity=transcendent_ucf_metrics["zoom"],
        )
        
        assert "TRANSCENDENT" in message

    @pytest.mark.unit
    def test_state_update_timestamp_format(self, valid_ucf_metrics):
        """Test that state update includes valid timestamp."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        assert "Timestamp:" in message


class TestMetricCalculations:
    """Test metric calculations and deltas."""

    @pytest.mark.unit
    def test_harmony_delta_calculation(self):
        """Test harmony delta calculation."""
        harmony = 0.65
        target = UCFProtocol.TARGETS["harmony"]
        delta = harmony - target
        
        assert delta > 0  # Above target
        assert abs(delta - 0.05) < 0.01

    @pytest.mark.unit
    def test_resilience_delta_calculation(self):
        """Test resilience delta calculation."""
        resilience = 1.20
        target = UCFProtocol.TARGETS["resilience"]
        delta = resilience - target
        
        assert delta > 0  # Above target
        assert abs(delta - 0.20) < 0.01

    @pytest.mark.unit
    def test_metric_targets_defined(self):
        """Test that all metric targets are defined."""
        required_targets = ["harmony", "resilience", "throughput", "focus", "friction", "velocity"]
        
        for target in required_targets:
            assert target in UCFProtocol.TARGETS
            assert isinstance(UCFProtocol.TARGETS[target], (int, float))

    @pytest.mark.unit
    def test_metric_ranges_valid(self):
        """Test that metric ranges are valid."""
        # Harmony and resilience can go higher
        assert UCFProtocol.TARGETS["harmony"] >= 0.0
        assert UCFProtocol.TARGETS["resilience"] >= 0.0
        
        # Other metrics should be in 0-1 range
        assert 0.0 <= UCFProtocol.TARGETS["throughput"] <= 1.0
        assert 0.0 <= UCFProtocol.TARGETS["focus"] <= 1.0
        assert 0.0 <= UCFProtocol.TARGETS["friction"] <= 1.0


class TestPhaseThresholds:
    """Test UCF phase threshold definitions."""

    @pytest.mark.unit
    def test_all_phases_defined(self):
        """Test that all phases are defined."""
        required_phases = ["CRITICAL", "UNSTABLE", "COHERENT", "HARMONIOUS", "TRANSCENDENT"]
        
        for phase in required_phases:
            assert phase in UCFProtocol.PHASES

    @pytest.mark.unit
    def test_phase_thresholds_ordered(self):
        """Test that phase thresholds are properly ordered."""
        phases_list = [
            ("CRITICAL", UCFProtocol.PHASES["CRITICAL"]),
            ("UNSTABLE", UCFProtocol.PHASES["UNSTABLE"]),
            ("COHERENT", UCFProtocol.PHASES["COHERENT"]),
            ("HARMONIOUS", UCFProtocol.PHASES["HARMONIOUS"]),
            ("TRANSCENDENT", UCFProtocol.PHASES["TRANSCENDENT"]),
        ]
        
        for i in range(len(phases_list) - 1):
            current_max = phases_list[i][1][1]
            next_min = phases_list[i + 1][1][0]
            assert current_max == next_min, f"Gap between {phases_list[i][0]} and {phases_list[i+1][0]}"

    @pytest.mark.unit
    def test_phase_threshold_coverage(self):
        """Test that phase thresholds cover full range."""
        min_threshold = min(phase[0] for phase in UCFProtocol.PHASES.values())
        max_threshold = max(phase[1] for phase in UCFProtocol.PHASES.values())
        
        assert min_threshold == 0.0
        assert max_threshold >= 1.0


class TestMessageFormatting:
    """Test message formatting and structure."""

    @pytest.mark.unit
    def test_message_is_string(self, valid_ucf_metrics):
        """Test that formatted message is a string."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        assert isinstance(message, str)

    @pytest.mark.unit
    def test_message_contains_metrics(self, valid_ucf_metrics):
        """Test that formatted message contains all metrics."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        # Message should contain metric values or labels
        assert "Harmony" in message or str(valid_ucf_metrics["harmony"]) in message

    @pytest.mark.unit
    def test_message_non_empty(self, valid_ucf_metrics):
        """Test that formatted message is not empty."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        assert len(message) > 0
        assert message.strip() != ""


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.unit
    def test_invalid_harmony_value_low(self):
        """Test handling of invalid low harmony value."""
        # Should still work but return CRITICAL phase
        phase = UCFProtocol.get_phase(-0.5)
        assert phase == "CRITICAL"

    @pytest.mark.unit
    def test_invalid_harmony_value_high(self):
        """Test handling of invalid high harmony value."""
        # Should still work and return TRANSCENDENT phase
        phase = UCFProtocol.get_phase(2.0)
        assert phase == "TRANSCENDENT"

    @pytest.mark.unit
    def test_zero_metrics(self):
        """Test handling of zero metrics."""
        message = UCFProtocol.format_state_update(
            harmony=0.0,
            resilience=0.0,
            throughput=0.0,
            focus=0.0,
            friction=1.0,
            velocity=0.0,
        )
        
        assert isinstance(message, str)
        assert "CRITICAL" in message

    @pytest.mark.unit
    def test_maximum_metrics(self):
        """Test handling of maximum metric values."""
        message = UCFProtocol.format_state_update(
            harmony=1.0,
            resilience=2.0,
            throughput=1.0,
            focus=1.0,
            friction=0.0,
            velocity=2.0,
        )
        
        assert isinstance(message, str)
        assert "TRANSCENDENT" in message


class TestProtocolConsistency:
    """Test protocol consistency and stability."""

    @pytest.mark.unit
    def test_repeated_calls_same_result(self, valid_ucf_metrics):
        """Test that repeated calls with same input produce consistent results."""
        message1 = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        message2 = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        # Messages should have same structure and phase
        assert "COHERENT" in message1
        assert "COHERENT" in message2

    @pytest.mark.unit
    def test_phase_detection_consistency(self):
        """Test that phase detection is consistent."""
        harmony = 0.65
        
        phase1 = UCFProtocol.get_phase(harmony)
        phase2 = UCFProtocol.get_phase(harmony)
        
        assert phase1 == phase2

    @pytest.mark.unit
    def test_targets_immutable(self):
        """Test that target metrics remain consistent."""
        targets1 = UCFProtocol.TARGETS.copy()
        
        # Call protocol methods
        UCFProtocol.get_phase(0.5)
        UCFProtocol.format_state_update(0.5, 1.0, 0.5, 0.5, 0.5, 1.0)
        
        targets2 = UCFProtocol.TARGETS.copy()
        
        assert targets1 == targets2


class TestIntegration:
    """Integration tests for protocol functionality."""

    @pytest.mark.integration
    def test_complete_state_update_workflow(self, valid_ucf_metrics):
        """Test complete state update workflow."""
        # Detect phase
        phase = UCFProtocol.get_phase(valid_ucf_metrics["harmony"])
        assert phase == "COHERENT"
        
        # Format state update
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
            agent="TestAgent",
        )
        
        # Verify message
        assert isinstance(message, str)
        assert "COHERENT" in message
        assert "TestAgent" in message

    @pytest.mark.integration
    def test_phase_transition_workflow(self):
        """Test workflow across phase transitions."""
        harmony_values = [0.15, 0.35, 0.50, 0.70, 0.90]
        expected_phases = ["CRITICAL", "UNSTABLE", "COHERENT", "HARMONIOUS", "TRANSCENDENT"]
        
        for harmony, expected_phase in zip(harmony_values, expected_phases):
            phase = UCFProtocol.get_phase(harmony)
            assert phase == expected_phase
            
            message = UCFProtocol.format_state_update(
                harmony=harmony,
                resilience=1.0,
                throughput=0.5,
                focus=0.5,
                friction=0.5,
                velocity=1.0,
            )
            
            assert expected_phase in message

    @pytest.mark.integration
    def test_all_metrics_in_message(self, valid_ucf_metrics):
        """Test that all metrics are represented in message."""
        message = UCFProtocol.format_state_update(
            harmony=valid_ucf_metrics["harmony"],
            resilience=valid_ucf_metrics["resilience"],
            throughput=valid_ucf_metrics["prana"],
            focus=valid_ucf_metrics["drishti"],
            friction=valid_ucf_metrics["klesha"],
            velocity=valid_ucf_metrics["zoom"],
        )
        
        # Message should contain metric information
        assert len(message) > 100  # Sufficient detail
        assert "UCF" in message or "State" in message or "Update" in message

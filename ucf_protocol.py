"""
UCF Protocol - Universal Coordination Framework Message Formatting
Helix Collective v15.3 Dual Resonance

Provides standardized message formatting for UCF state updates, agent communications,
and system-wide coordination metrics.
"""

import json
from datetime import UTC, datetime
from typing import Any

import logging

logger = logging.getLogger(__name__)


class UCFProtocol:
    """
    UCF Protocol handler for formatting coordination state messages.

    Metrics:
    - Harmony: System-wide coherence (0.0 - 1.0)
    - Resilience: Recovery capability (0.0 - 2.0)
    - Throughput: Energy/vitality (0.0 - 1.0)
    - Focus: Clarity/focus (0.0 - 1.0)
    - Friction: Suffering/friction (0.0 - 1.0, lower is better)
    - Velocity: Perspective/scale (0.0 - 2.0)
    """

    # UCF Phase thresholds
    PHASES = {
        "CRITICAL": (0.0, 0.30),
        "UNSTABLE": (0.30, 0.45),
        "COHERENT": (0.45, 0.60),
        "HARMONIOUS": (0.60, 0.80),
        "TRANSCENDENT": (0.80, 1.0),
    }

    # Target metrics
    TARGETS = {
        "harmony": 0.60,
        "resilience": 1.0,
        "throughput": 0.70,
        "focus": 0.70,
        "friction": 0.05,
        "velocity": 1.0,
    }

    @staticmethod
    def get_phase(harmony: float) -> str:
        """Determine UCF phase from harmony level."""
        for phase, (min_val, max_val) in UCFProtocol.PHASES.items():
            if min_val <= harmony < max_val:
                return phase
        return "TRANSCENDENT" if harmony >= 0.80 else "CRITICAL"

    @staticmethod
    def format_state_update(
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
        context: str | None = None,
        agent: str | None = None,
    ) -> str:
        """
        Format a UCF state update message.

        Args:
            harmony: System coherence (0.0 - 1.0)
            resilience: Recovery capability (0.0 - 2.0)
            throughput: Energy level (0.0 - 1.0)
            focus: Clarity (0.0 - 1.0)
            friction: Suffering (0.0 - 1.0, lower is better)
            velocity: Perspective (0.0 - 2.0)
            context: Optional context for the update
            agent: Optional agent name reporting the update

        Returns:
            Formatted UCF state message
        """
        phase = UCFProtocol.get_phase(harmony)
        timestamp = datetime.now(UTC).isoformat()

        # Calculate deltas from targets
        harmony_delta = harmony - UCFProtocol.TARGETS["harmony"]
        resilience_delta = resilience - UCFProtocol.TARGETS["resilience"]

        # Build message
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║              UCF STATE UPDATE                             ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║ Timestamp: {timestamp:44} ║",
            f"║ Phase: {phase:51} ║",
        ]

        if agent:
            lines.append(f"║ Agent: {agent:51} ║")

        if context:
            lines.append(f"║ Context: {context[:49]:49} ║")

        lines.extend(
            [
                "╠═══════════════════════════════════════════════════════════╣",
                "║ METRICS                                                   ║",
                "╠═══════════════════════════════════════════════════════════╣",
                f"║ Harmony:     {harmony:6.4f}  {'▲' if harmony_delta >= 0 else '▼'} {abs(harmony_delta):6.4f}  (target: {UCFProtocol.TARGETS['harmony']:.2f}) ║",
                f"║ Resilience:  {resilience:6.4f}  {'▲' if resilience_delta >= 0 else '▼'} {abs(resilience_delta):6.4f}  (target: {UCFProtocol.TARGETS['resilience']:.2f}) ║",
                f"║ Throughput:       {throughput:6.4f}                    (target: {UCFProtocol.TARGETS['throughput']:.2f}) ║",
                f"║ Focus:     {focus:6.4f}                    (target: {UCFProtocol.TARGETS['focus']:.2f}) ║",
                f"║ Friction:      {friction:6.4f}                    (target: {UCFProtocol.TARGETS['friction']:.2f}) ║",
                f"║ Velocity:        {velocity:6.4f}                    (target: {UCFProtocol.TARGETS['velocity']:.2f}) ║",
                "╚═══════════════════════════════════════════════════════════╝",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def format_compact_state(
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
    ) -> str:
        """
        Format a compact single-line UCF state.

        Returns:
            Compact state string like: "UCF: H=0.4922 R=1.1191 P=0.5075 D=0.5023 K=0.011 Z=1.0228 [COHERENT]"
        """
        phase = UCFProtocol.get_phase(harmony)
        return (
            f"UCF: H={harmony:.4f} R={resilience:.4f} P={throughput:.4f} "
            f"D={focus:.4f} K={friction:.4f} Z={velocity:.4f} [{phase}]"
        )

    @staticmethod
    def format_agent_message(
        agent_name: str,
        message: str,
        ucf_state: dict[str, float] | None = None,
        message_type: str = "INFO",
    ) -> str:
        """
        Format an agent communication message with optional UCF context.

        Args:
            agent_name: Name of the agent
            message: Message content
            ucf_state: Optional UCF state dict
            message_type: Message type (INFO, WARNING, ERROR, SUCCESS)

        Returns:
            Formatted agent message
        """
        timestamp = datetime.now(UTC).isoformat()

        # Message type emoji
        type_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}.get(message_type, "📝")

        lines = [f"{type_emoji} [{agent_name}] {timestamp}", f"{message}"]

        if ucf_state:
            compact_state = UCFProtocol.format_compact_state(
                ucf_state.get("harmony", 0.0),
                ucf_state.get("resilience", 0.0),
                ucf_state.get("throughput", 0.0),
                ucf_state.get("focus", 0.0),
                ucf_state.get("friction", 0.0),
                ucf_state.get("velocity", 0.0),
            )
            lines.append(f"   {compact_state}")

        return "\n".join(lines)

    @staticmethod
    def format_cycle_invocation(
        cycle_name: str,
        agent_name: str,
        intention: str,
        ucf_before: dict[str, float],
        ucf_after: dict[str, float] | None = None,
    ) -> str:
        """
        Format a Coordination Cycle invocation message.

        Args:
            cycle_name: Name of the cycle
            agent_name: Agent performing the cycle
            intention: Cycle intention
            ucf_before: UCF state before cycle
            ucf_after: Optional UCF state after cycle

        Returns:
            Formatted routine message
        """
        timestamp = datetime.now(UTC).isoformat()

        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║           COORDINATION CYCLE INVOCATION                        ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║ Cycle: {cycle_name[:52]:52} ║",
            f"║ Agent: {agent_name[:53]:53} ║",
            f"║ Time: {timestamp:54} ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║ Intention: {intention[:49]:49} ║",
            "╠═══════════════════════════════════════════════════════════╣",
            "║ UCF STATE (BEFORE)                                        ║",
            "╠═══════════════════════════════════════════════════════════╣",
        ]

        # Add before state
        before_compact = UCFProtocol.format_compact_state(
            ucf_before.get("harmony", 0.0),
            ucf_before.get("resilience", 0.0),
            ucf_before.get("throughput", 0.0),
            ucf_before.get("focus", 0.0),
            ucf_before.get("friction", 0.0),
            ucf_before.get("velocity", 0.0),
        )
        lines.append(f"║ {before_compact:57} ║")

        # Add after state if provided
        if ucf_after:
            lines.extend(
                [
                    "╠═══════════════════════════════════════════════════════════╣",
                    "║ UCF STATE (AFTER)                                         ║",
                    "╠═══════════════════════════════════════════════════════════╣",
                ]
            )

            after_compact = UCFProtocol.format_compact_state(
                ucf_after.get("harmony", 0.0),
                ucf_after.get("resilience", 0.0),
                ucf_after.get("throughput", 0.0),
                ucf_after.get("focus", 0.0),
                ucf_after.get("friction", 0.0),
                ucf_after.get("velocity", 0.0),
            )
            lines.append(f"║ {after_compact:57} ║")

            # Calculate deltas
            harmony_delta = ucf_after.get("harmony", 0.0) - ucf_before.get("harmony", 0.0)
            lines.extend(
                [
                    "╠═══════════════════════════════════════════════════════════╣",
                    f"║ Harmony Delta: {harmony_delta:+.4f}                              ║",
                ]
            )

        lines.append("╚═══════════════════════════════════════════════════════════╝")

        return "\n".join(lines)

    @staticmethod
    def to_json(
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Export UCF state as JSON.

        Args:
            harmony: System coherence
            resilience: Recovery capability
            throughput: Energy level
            focus: Clarity
            friction: Suffering
            velocity: Perspective
            metadata: Optional additional metadata

        Returns:
            JSON string of UCF state
        """
        state = {
            "timestamp": datetime.now(UTC).isoformat(),
            "phase": UCFProtocol.get_phase(harmony),
            "metrics": {
                "harmony": harmony,
                "resilience": resilience,
                "throughput": throughput,
                "focus": focus,
                "friction": friction,
                "velocity": velocity,
            },
            "targets": UCFProtocol.TARGETS,
            "deltas": {
                "harmony": harmony - UCFProtocol.TARGETS["harmony"],
                "resilience": resilience - UCFProtocol.TARGETS["resilience"],
                "throughput": throughput - UCFProtocol.TARGETS["throughput"],
                "focus": focus - UCFProtocol.TARGETS["focus"],
                "friction": friction - UCFProtocol.TARGETS["friction"],
                "velocity": velocity - UCFProtocol.TARGETS["velocity"],
            },
        }

        if metadata:
            state["metadata"] = metadata

        return json.dumps(state, indent=2)


# Example usage
if __name__ == "__main__":
    # Test state update formatting
    logger.info(
        UCFProtocol.format_state_update(
            harmony=0.4922,
            resilience=1.1191,
            throughput=0.5075,
            focus=0.5023,
            friction=0.011,
            velocity=1.0228,
            context="System initialization",
            agent="Omega Zero",
        )
    )

    logger.info("\n" + "=" * 60 + "\n")

    # Test compact format
    logger.info(
        UCFProtocol.format_compact_state(
            harmony=0.4922,
            resilience=1.1191,
            throughput=0.5075,
            focus=0.5023,
            friction=0.011,
            velocity=1.0228,
        )
    )

    logger.info("\n" + "=" * 60 + "\n")

    # Test agent message
    ucf_state = {
        "harmony": 0.4922,
        "resilience": 1.1191,
        "throughput": 0.5075,
        "focus": 0.5023,
        "friction": 0.011,
        "velocity": 1.0228,
    }

    logger.info(
        UCFProtocol.format_agent_message(
            agent_name="Arjuna",
            message="Deployment verification complete. All systems operational.",
            ucf_state=ucf_state,
            message_type="SUCCESS",
        )
    )

    logger.info("\n" + "=" * 60 + "\n")

    # Test routine
    logger.info(
        UCFProtocol.format_cycle_invocation(
            cycle_name="Harmony Restoration",
            agent_name="Omega Zero",
            intention="Restore system coherence after deployment",
            ucf_before=ucf_state,
            ucf_after={
                "harmony": 0.5234,
                "resilience": 1.1191,
                "throughput": 0.5075,
                "focus": 0.5023,
                "friction": 0.009,
                "velocity": 1.0228,
            },
        )
    )

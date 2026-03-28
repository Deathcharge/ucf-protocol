"""
UCF Tracker - Historical Harmony Data and Trend Analysis
Helix Collective v15.3 Dual Resonance

Tracks UCF metrics over time, analyzes trends, and provides predictions
for harmony evolution. Enables proactive maintenance and cycle scheduling.
"""

import sqlite3
import statistics
from datetime import UTC, datetime, timedelta
from pathlib import Path

import logging

logger = logging.getLogger(__name__)


class UCFTracker:
    """
    Tracks and analyzes UCF metrics over time.
    """

    def __init__(self, db_path: str = "backend/state/ucf_history.db"):
        """
        Initialize UCF tracker with database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ucf_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                harmony REAL NOT NULL,
                resilience REAL NOT NULL,
                throughput REAL NOT NULL,
                focus REAL NOT NULL,
                friction REAL NOT NULL,
                velocity REAL NOT NULL,
                phase TEXT NOT NULL,
                context TEXT,
                agent TEXT
            )
        """
        )

        # Create routines table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS optimization_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cycle_name TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                intention TEXT,
                harmony_before REAL NOT NULL,
                harmony_after REAL NOT NULL,
                success INTEGER NOT NULL
            )
        """
        )

        # Create index on timestamp for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
            ON ucf_metrics(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cycles_timestamp
            ON optimization_cycles(timestamp)
        """
        )

        conn.commit()
        conn.close()

    def record_metrics(
        self,
        harmony: float,
        resilience: float,
        throughput: float,
        focus: float,
        friction: float,
        velocity: float,
        phase: str,
        context: str | None = None,
        agent: str | None = None,
    ) -> int:
        """
        Record UCF metrics to database.

        Args:
            harmony: System coherence
            resilience: Recovery capability
            throughput: Energy level
            focus: Clarity
            friction: Suffering
            velocity: Perspective
            phase: UCF phase
            context: Optional context
            agent: Optional agent name

        Returns:
            Record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now(UTC).isoformat()

        cursor.execute(
            """
            INSERT INTO ucf_metrics
            (timestamp, harmony, resilience, throughput, focus, friction, velocity, phase, context, agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                timestamp,
                harmony,
                resilience,
                throughput,
                focus,
                friction,
                velocity,
                phase,
                context,
                agent,
            ),
        )

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def record_cycle(
        self,
        cycle_name: str,
        agent_name: str,
        harmony_before: float,
        harmony_after: float,
        success: bool,
        intention: str | None = None,
    ) -> int:
        """
        Record cycle execution to database.

        Args:
            cycle_name: Name of the cycle
            agent_name: Agent performing cycle
            harmony_before: Harmony before cycle
            harmony_after: Harmony after cycle
            success: Whether cycle succeeded
            intention: Optional cycle intention

        Returns:
            Record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now(UTC).isoformat()

        cursor.execute(
            """
            INSERT INTO optimization_cycles
            (timestamp, cycle_name, agent_name, intention, harmony_before, harmony_after, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                timestamp,
                cycle_name,
                agent_name,
                intention,
                harmony_before,
                harmony_after,
                int(success),
            ),
        )

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def get_recent_metrics(self, limit: int = 100) -> list[dict]:
        """
        Get recent UCF metrics.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of metric dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, harmony, resilience, throughput, focus, friction, velocity, phase, context, agent
            FROM ucf_metrics
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()
        conn.close()

        metrics = []
        for row in rows:
            metrics.append(
                {
                    "timestamp": row[0],
                    "harmony": row[1],
                    "resilience": row[2],
                    "throughput": row[3],
                    "focus": row[4],
                    "friction": row[5],
                    "velocity": row[6],
                    "phase": row[7],
                    "context": row[8],
                    "agent": row[9],
                }
            )

        return metrics

    def get_metrics_in_range(self, start_time: datetime, end_time: datetime) -> list[dict]:
        """
        Get UCF metrics within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of metric dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, harmony, resilience, throughput, focus, friction, velocity, phase, context, agent
            FROM ucf_metrics
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        rows = cursor.fetchall()
        conn.close()

        metrics = []
        for row in rows:
            metrics.append(
                {
                    "timestamp": row[0],
                    "harmony": row[1],
                    "resilience": row[2],
                    "throughput": row[3],
                    "focus": row[4],
                    "friction": row[5],
                    "velocity": row[6],
                    "phase": row[7],
                    "context": row[8],
                    "agent": row[9],
                }
            )

        return metrics

    def get_harmony_trend(self, hours: int = 24) -> dict:
        """
        Analyze harmony trend over specified hours.

        Args:
            hours: Number of hours to analyze

        Returns:
            Trend analysis dictionary
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours)

        metrics = self.get_metrics_in_range(start_time, end_time)

        if not metrics:
            return {
                "trend": "UNKNOWN",
                "direction": "STABLE",
                "current": 0.0,
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
                "change": 0.0,
                "data_points": 0,
            }

        harmony_values = [m["harmony"] for m in metrics]

        current = harmony_values[-1] if harmony_values else 0.0
        average = statistics.mean(harmony_values) if harmony_values else 0.0
        min_val = min(harmony_values) if harmony_values else 0.0
        max_val = max(harmony_values) if harmony_values else 0.0

        # Calculate change from first to last
        change = harmony_values[-1] - harmony_values[0] if len(harmony_values) > 1 else 0.0

        # Determine direction
        if change > 0.01:
            direction = "RISING"
        elif change < -0.01:
            direction = "FALLING"
        else:
            direction = "STABLE"

        # Determine trend
        if current >= 0.60:
            trend = "HARMONIOUS"
        elif current >= 0.45:
            trend = "COHERENT"
        elif current >= 0.30:
            trend = "UNSTABLE"
        else:
            trend = "CRITICAL"

        return {
            "trend": trend,
            "direction": direction,
            "current": current,
            "average": average,
            "min": min_val,
            "max": max_val,
            "change": change,
            "data_points": len(harmony_values),
            "timespan_hours": hours,
        }

    def predict_harmony(self, hours_ahead: int = 24) -> dict:
        """
        Predict future harmony using simple linear regression.

        Args:
            hours_ahead: Hours to predict ahead

        Returns:
            Prediction dictionary
        """
        # Get last 48 hours of data
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=48)

        metrics = self.get_metrics_in_range(start_time, end_time)

        if len(metrics) < 2:
            return {
                "predicted_harmony": 0.0,
                "confidence": "LOW",
                "hours_ahead": hours_ahead,
                "data_points": len(metrics),
            }

        # Simple linear regression
        harmony_values = [m["harmony"] for m in metrics]
        n = len(harmony_values)

        # Calculate slope
        x_values = list(range(n))
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(harmony_values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, harmony_values, strict=False))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        # Predict future value
        future_x = n + (hours_ahead / (48 / n))  # Scale to data point spacing
        predicted = slope * future_x + intercept

        # Clamp to valid range
        predicted = max(0.0, min(1.0, predicted))

        # Calculate confidence based on data variance
        variance = statistics.variance(harmony_values) if len(harmony_values) > 1 else 1.0

        if variance < 0.01:
            confidence = "HIGH"
        elif variance < 0.05:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return {
            "predicted_harmony": predicted,
            "confidence": confidence,
            "hours_ahead": hours_ahead,
            "data_points": n,
            "slope": slope,
            "current": harmony_values[-1],
        }

    def get_cycle_history(self, limit: int = 50) -> list[dict]:
        """
        Get recent cycle history.

        Args:
            limit: Maximum number of records

        Returns:
            List of cycle dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, cycle_name, agent_name, intention,
                   harmony_before, harmony_after, success
            FROM optimization_cycles
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()
        conn.close()

        optimization_cycles = []
        for row in rows:
            optimization_cycles.append(
                {
                    "timestamp": row[0],
                    "cycle_name": row[1],
                    "agent_name": row[2],
                    "intention": row[3],
                    "harmony_before": row[4],
                    "harmony_after": row[5],
                    "success": bool(row[6]),
                    "delta": row[5] - row[4],
                }
            )

        return optimization_cycles

    def get_cycle_effectiveness(self, cycle_name: str) -> dict:
        """
        Analyze effectiveness of a specific cycle.

        Args:
            cycle_name: Name of the cycle

        Returns:
            Effectiveness analysis dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT harmony_before, harmony_after, success
            FROM optimization_cycles
            WHERE cycle_name = ?
        """,
            (cycle_name,),
        )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {
                "cycle_name": cycle_name,
                "executions": 0,
                "success_rate": 0.0,
                "average_delta": 0.0,
                "effectiveness": "UNKNOWN",
            }

        deltas = [after - before for before, after, _ in rows]
        successes = sum(1 for _, _, success in rows if success)

        executions = len(rows)
        success_rate = successes / executions if executions > 0 else 0.0
        average_delta = statistics.mean(deltas) if deltas else 0.0

        # Determine effectiveness
        if success_rate >= 0.8 and average_delta >= 0.05:
            effectiveness = "HIGHLY EFFECTIVE"
        elif success_rate >= 0.6 and average_delta >= 0.02:
            effectiveness = "EFFECTIVE"
        elif success_rate >= 0.4:
            effectiveness = "MODERATELY EFFECTIVE"
        else:
            effectiveness = "LOW EFFECTIVENESS"

        return {
            "cycle_name": cycle_name,
            "executions": executions,
            "success_rate": success_rate,
            "average_delta": average_delta,
            "effectiveness": effectiveness,
            "min_delta": min(deltas) if deltas else 0.0,
            "max_delta": max(deltas) if deltas else 0.0,
        }

    def should_trigger_cycle(self, harmony_threshold: float = 0.40) -> tuple[bool, str]:
        """
        Determine if a cycle should be triggered based on harmony.

        Args:
            harmony_threshold: Threshold below which to trigger cycle

        Returns:
            Tuple of (should_trigger, reason)
        """
        recent = self.get_recent_metrics(limit=1)

        if not recent:
            return False, "No recent metrics available"

        current_harmony = recent[0]["harmony"]

        if current_harmony < harmony_threshold:
            return (
                True,
                f"Harmony {current_harmony:.4f} below threshold {harmony_threshold:.4f}",
            )

        # Check trend
        trend = self.get_harmony_trend(hours=6)

        if trend["direction"] == "FALLING" and trend["change"] < -0.05:
            return True, "Harmony falling rapidly (change: {:.4f})".format(trend["change"])

        # Check prediction
        prediction = self.predict_harmony(hours_ahead=12)

        if prediction["predicted_harmony"] < harmony_threshold:
            return (
                True,
                "Predicted harmony {:.4f} below threshold".format(prediction["predicted_harmony"]),
            )

        return False, "System stable"


# Example usage
if __name__ == "__main__":
    tracker = UCFTracker()

    # Record some test metrics
    logger.info("Recording test metrics...")
    tracker.record_metrics(
        harmony=0.4922,
        resilience=1.1191,
        throughput=0.5075,
        focus=0.5023,
        friction=0.011,
        velocity=1.0228,
        phase="COHERENT",
        context="System initialization",
        agent="Omega Zero",
    )

    # Get recent metrics
    logger.info("\nRecent metrics:")
    recent = tracker.get_recent_metrics(limit=5)
    for metric in recent:
        logger.info("  {}: harmony={:.4f}, phase={}".format(metric["timestamp"], metric["harmony"], metric["phase"]))

    # Analyze trend
    logger.info("\nHarmony trend (24h):")
    trend = tracker.get_harmony_trend(hours=24)
    for key, value in trend.items():
        logger.info("  %s: %s", key, value)

    # Check if cycle should be triggered
    logger.info("\nRoutine trigger check:")
    should_trigger, reason = tracker.should_trigger_cycle(harmony_threshold=0.50)
    logger.info("  Should trigger: %s", should_trigger)
    logger.info("  Reason: %s", reason)

# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import time
import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Predicts next user actions using weighted Markov chains."""

    def __init__(self, database=None, config: dict = None):
        self.db = database
        self.config = config or {}

        # In-memory transition matrix
        self._transitions: dict[str, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        self._time_weighted: dict[tuple[str, str, int], float] = {}

        # Prediction accuracy tracking
        self._recent_predictions: list[bool] = []
        self._max_history = self.config.get("max_history_events", 100)
        self._time_bucket_minutes = self.config.get("time_bucket_minutes", 30)

        self._last_app: str = ""
        self._last_prediction: str = ""

        # Routine detection
        self._hourly_routines: dict[tuple[int, str], int] = defaultdict(int)

        # Load existing data
        self._load_transitions()
        logger.info("PredictionEngine initialized")

    def _load_transitions(self):
        """Load transition counts from database into memory."""
        if not self.db:
            return
        try:
            rows = self.db.fetch_all(
                "SELECT from_app, to_app, count, time_bucket FROM transition_counts"
            )
            for from_app, to_app, count, time_bucket in rows:
                self._transitions[from_app][to_app] += count
                key = (from_app, to_app, time_bucket or -1)
                self._time_weighted[key] = self._time_weighted.get(key, 0) + count
        except Exception as e:
            logger.warning("Failed to load transitions: %s", e)

    def _get_time_bucket(self, timestamp: float = None) -> int:
        """Convert timestamp to half-hour bucket (0-47)."""
        if timestamp is None:
            timestamp = time.time()
        dt = datetime.fromtimestamp(timestamp)
        return dt.hour * 2 + (1 if dt.minute >= 30 else 0)

    def record_transition(self, from_app: str, to_app: str):
        """Record an application transition."""
        if not from_app or not to_app or from_app == to_app:
            return

        time_bucket = self._get_time_bucket()

        self._transitions[from_app][to_app] += 1
        key = (from_app, to_app, time_bucket)
        self._time_weighted[key] = self._time_weighted.get(key, 0) + 1

        # Track hourly routines
        hour = datetime.fromtimestamp(time.time()).hour
        self._hourly_routines[(hour, to_app)] += 1

        # Persist to database
        if self.db:
            try:
                self.db.execute(
                    """INSERT INTO transition_counts (from_app, to_app, count, time_bucket)
                       VALUES (?, ?, 1, ?)
                       ON CONFLICT(from_app, to_app, time_bucket)
                       DO UPDATE SET count = count + 1""",
                    (from_app, to_app, time_bucket)
                )
            except Exception as e:
                logger.debug("Failed to persist transition: %s", e)

        # Track prediction accuracy
        if self._last_prediction and self._last_prediction == to_app:
            self._recent_predictions.append(True)
        elif self._last_prediction:
            self._recent_predictions.append(False)

        if len(self._recent_predictions) > self._max_history:
            self._recent_predictions.pop(0)

        self._last_app = to_app

    def predict_next(self, current_app: str, time_alpha: float = 2.0) -> str:
        """Predict the most likely next application."""
        if current_app not in self._transitions:
            return ""

        time_bucket = self._get_time_bucket()
        candidates = self._transitions[current_app]

        if not candidates:
            return ""

        best_app = ""
        best_score = -1.0

        for app, base_count in candidates.items():
            time_key = (current_app, app, time_bucket)
            time_count = self._time_weighted.get(time_key, 0)
            score = base_count + (time_alpha * time_count)
            if score > best_score:
                best_score = score
                best_app = app

        self._last_prediction = best_app
        return best_app

    def get_accuracy(self) -> float:
        """Return moving average accuracy of recent predictions."""
        if not self._recent_predictions:
            return 0.0
        return sum(self._recent_predictions) / len(self._recent_predictions)

    def detect_routines(self, min_occurrences: int = 5) -> list[dict]:
        """Detect time-based application usage routines."""
        routines = []
        for (hour, app), count in self._hourly_routines.items():
            if count >= min_occurrences:
                routines.append({
                    "hour": hour,
                    "application": app,
                    "occurrences": count,
                    "confidence": min(count / min_occurrences, 1.0)
                })
        routines.sort(key=lambda r: r["confidence"], reverse=True)
        return routines

    def get_confidence(self) -> float:
        """Return current prediction confidence (0.0 to 1.0)."""
        return self.get_accuracy()

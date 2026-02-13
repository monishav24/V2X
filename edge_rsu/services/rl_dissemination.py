"""
SmartV2X-CP Ultra — RL-Based Dissemination Decision Module
============================================================
Uses a simple Q-learning agent to decide which vehicles should
receive collision warnings based on risk level, channel capacity,
and past warning effectiveness.
"""

import random
import logging
from typing import Dict, Any, List, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class RLDisseminator:
    """
    Reinforcement Learning agent for warning dissemination.

    States:  (risk_level, channel_load_bin)
    Actions: WARN, SKIP
    Reward:  +1 for effective warning (risk reduced), -0.5 for unnecessary
    """

    ACTIONS = ["WARN", "SKIP"]

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount: float = 0.95,
        epsilon: float = 0.15,
        max_channel_capacity: int = 50,
    ):
        self.lr = learning_rate
        self.gamma = discount
        self.epsilon = epsilon
        self.max_capacity = max_channel_capacity

        # Q-table: {state: {action: value}}
        self._q_table: Dict[Tuple, Dict[str, float]] = defaultdict(
            lambda: {"WARN": 0.0, "SKIP": 0.0}
        )
        self._current_warnings = 0
        self._total_decisions = 0

    # ── State representation ──────────────────────────────
    @staticmethod
    def _get_state(risk_level: str, channel_load: float) -> Tuple:
        load_bin = "LOW" if channel_load < 0.4 else ("MED" if channel_load < 0.75 else "HIGH")
        return (risk_level, load_bin)

    # ── Decision ──────────────────────────────────────────
    def decide(
        self,
        vehicle_id: str,
        risk_level: str,
        risk_score: float,
    ) -> str:
        """
        Decide whether to WARN or SKIP a vehicle.

        Parameters
        ----------
        vehicle_id : target vehicle
        risk_level : LOW / MEDIUM / HIGH
        risk_score : 0.0–1.0

        Returns
        -------
        action : "WARN" or "SKIP"
        """
        channel_load = self._current_warnings / max(self.max_capacity, 1)
        state = self._get_state(risk_level, channel_load)

        # ε-greedy policy
        if random.random() < self.epsilon:
            action = random.choice(self.ACTIONS)
        else:
            q_vals = self._q_table[state]
            action = max(q_vals, key=q_vals.get)

        if action == "WARN":
            self._current_warnings += 1

        self._total_decisions += 1
        return action

    def update(
        self,
        risk_level: str,
        channel_load: float,
        action: str,
        reward: float,
        next_risk_level: str,
        next_channel_load: float,
    ):
        """Q-learning update after observing outcome."""
        state = self._get_state(risk_level, channel_load)
        next_state = self._get_state(next_risk_level, next_channel_load)

        current_q = self._q_table[state][action]
        next_max_q = max(self._q_table[next_state].values())

        new_q = current_q + self.lr * (reward + self.gamma * next_max_q - current_q)
        self._q_table[state][action] = new_q

    def batch_decide(
        self,
        risk_records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Decide for a batch of risk records.
        Returns list with added 'action' field.
        """
        results = []
        for record in risk_records:
            action = self.decide(
                vehicle_id=record.get("vehicle_a", ""),
                risk_level=record.get("risk_level", "LOW"),
                risk_score=record.get("risk_score", 0.0),
            )
            results.append({**record, "action": action})
        return results

    def reset_epoch(self):
        """Reset per-epoch counters (call at each decision cycle)."""
        self._current_warnings = 0

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_decisions": self._total_decisions,
            "q_table_size": len(self._q_table),
            "epsilon": self.epsilon,
        }

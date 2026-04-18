from __future__ import annotations
import os
import sqlite3
from datetime import date
from typing import Dict, Tuple


class BudgetManager:
    def __init__(self, daily_limit: float = 3.0) -> None:
        self.daily_limit = daily_limit
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self._db_path = os.path.join(data_dir, "dp_budget.sqlite3")
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS budget_usage ("
                "  user_id TEXT NOT NULL,"
                "  usage_date TEXT NOT NULL,"
                "  spent REAL NOT NULL DEFAULT 0,"
                "  PRIMARY KEY (user_id, usage_date)"
                ")"
            )

    def _spent(self, user_id: str, today: date) -> float:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT spent FROM budget_usage WHERE user_id = ? AND usage_date = ?",
                (user_id, today.isoformat()),
            ).fetchone()
            return row[0] if row else 0.0

    def can_spend(self, user_id: str, epsilon: float, today: date) -> bool:
        spent = self._spent(user_id, today)
        return spent + epsilon <= self.daily_limit

    def spend(self, user_id: str, epsilon: float, today: date) -> None:
        spent = self._spent(user_id, today)
        new_value = spent + epsilon
        if new_value > self.daily_limit:
            raise ValueError("Privacy budget exceeded")
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO budget_usage (user_id, usage_date, spent) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, usage_date) DO UPDATE SET spent = ?",
                (user_id, today.isoformat(), new_value, new_value),
            )

    def get_spent(self, user_id: str, today: date) -> float:
        return self._spent(user_id, today)

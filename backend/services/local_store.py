"""
Local JSON-based persistence for recent results and user context.
This provides a simple local database without external dependencies.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


class LocalStore:
    """
    Thread-safe JSON file store for:
    - suppliers
    - opportunities
    - events
    - materials
    - user_context
    """

    def __init__(self, path: str = "./data/local_store.json"):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({
                    "suppliers": {},
                    "opportunities": {},
                    "events": {},
                    "materials": {},
                    "user_context": {}
                }, f)

    # ---------- internal helpers ----------
    def _read(self) -> Dict[str, Any]:
        with self._lock:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data: Dict[str, Any]):
        with self._lock:
            tmp_path = self.path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.path)

    def _now(self) -> str:
        return datetime.now().isoformat()

    # ---------- suppliers ----------
    def save_suppliers(self, user_id: str, suppliers: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None):
        data = self._read()
        user_key = user_id or "anonymous"
        data.setdefault("suppliers", {})
        data["suppliers"][user_key] = {
            "updated_at": self._now(),
            "items": suppliers or [],
            "context": context or {}
        }
        self._write(data)

    def get_suppliers(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        data = self._read()
        user_key = user_id or "anonymous"
        items = data.get("suppliers", {}).get(user_key, {}).get("items", [])
        return items[:limit]

    # ---------- opportunities ----------
    def save_opportunities(self, user_id: str, opportunities: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None):
        data = self._read()
        user_key = user_id or "anonymous"
        data.setdefault("opportunities", {})
        data["opportunities"][user_key] = {
            "updated_at": self._now(),
            "items": opportunities or [],
            "context": context or {}
        }
        self._write(data)

    def get_opportunities(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        data = self._read()
        user_key = user_id or "anonymous"
        items = data.get("opportunities", {}).get(user_key, {}).get("items", [])
        return items[:limit]

    # ---------- events ----------
    def save_events(self, user_id: str, events: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None):
        data = self._read()
        user_key = user_id or "anonymous"
        data.setdefault("events", {})
        data["events"][user_key] = {
            "updated_at": self._now(),
            "items": events or [],
            "context": context or {}
        }
        self._write(data)

    def get_events(self, user_id: str, limit: int = 100, city: Optional[str] = None,
                   date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self._read()
        user_key = user_id or "anonymous"
        items: List[Dict[str, Any]] = data.get("events", {}).get(user_key, {}).get("items", [])

        def in_date_range(item: Dict[str, Any]) -> bool:
            if not date_from and not date_to:
                return True
            try:
                dt_str = item.get("date") or item.get("start_date") or item.get("when")
                if not dt_str:
                    return True
                dt = datetime.fromisoformat(str(dt_str).split(" ")[0])
                if date_from and dt < datetime.fromisoformat(date_from):
                    return False
                if date_to and dt > datetime.fromisoformat(date_to):
                    return False
                return True
            except Exception:
                return True

        def city_match(item: Dict[str, Any]) -> bool:
            if not city:
                return True
            loc = item.get("location") or {}
            return str(loc.get("city", "")).lower().strip() == city.lower().strip()

        filtered = [e for e in items if city_match(e) and in_date_range(e)]
        return filtered[:limit]

    # ---------- materials ----------
    def save_materials(self, user_id: str, materials: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None):
        data = self._read()
        user_key = user_id or "anonymous"
        data.setdefault("materials", {})
        data["materials"][user_key] = {
            "updated_at": self._now(),
            "items": materials or [],
            "context": context or {}
        }
        self._write(data)

    def get_materials(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        data = self._read()
        user_key = user_id or "anonymous"
        items = data.get("materials", {}).get(user_key, {}).get("items", [])
        return items[:limit]

    # ---------- user context ----------
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        data = self._read()
        user_key = user_id or "anonymous"
        return data.get("user_context", {}).get(user_key, {})

    def update_user_context(self, user_id: str, context: Dict[str, Any]):
        data = self._read()
        user_key = user_id or "anonymous"
        all_ctx = data.setdefault("user_context", {})
        updated = {**all_ctx.get(user_key, {}), **(context or {}), "updated_at": self._now()}
        all_ctx[user_key] = updated
        self._write(data)


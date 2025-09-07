"""
History API endpoints for persisting analysis results for the unified dashboard.

Stores a simple JSON list on disk (data/history.json) to persist recent
analyses across sessions without requiring a database.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/history", tags=["history"])


def _data_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _history_path() -> str:
    return os.path.join(_data_dir(), "history.json")


def _ensure_storage() -> None:
    d = _data_dir()
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    p = _history_path()
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            json.dump([], f)


def _load_history() -> List[Dict[str, Any]]:
    _ensure_storage()
    with open(_history_path(), "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except json.JSONDecodeError:
            return []


def _save_history(items: List[Dict[str, Any]]) -> None:
    _ensure_storage()
    with open(_history_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))


@router.get("")
async def get_history() -> Dict[str, Any]:
    items = _load_history()
    return {"success": True, "items": items}


@router.post("")
async def add_history(item: Dict[str, Any]) -> Dict[str, Any]:
    # Basic validation
    required = ["ts", "trust_score", "classification"]
    if not all(k in item for k in required):
        raise HTTPException(status_code=400, detail="Missing required fields")
    try:
        # Normalize
        item["ts"] = item.get("ts") or datetime.utcnow().isoformat()
        item["trust_score"] = int(item.get("trust_score", 0))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item format")

    items = _load_history()
    items.insert(0, item)
    # Keep last 200 to avoid uncontrolled growth
    items = items[:200]
    _save_history(items)
    return {"success": True, "count": len(items)}


@router.delete("")
async def clear_history() -> Dict[str, Any]:
    _save_history([])
    return {"success": True, "cleared": True}


@router.get("/overview")
async def history_overview() -> Dict[str, Any]:
    items = _load_history()
    total = len(items)
    if total == 0:
        return {"success": True, "total": 0, "flagged": 0, "avg": 0}
    scores = [int(i.get("trust_score", 0)) for i in items]
    flagged = sum(1 for s in scores if s < 40)
    avg = round(sum(scores) / total)
    return {"success": True, "total": total, "flagged": flagged, "avg": avg}


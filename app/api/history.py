from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException

from app.db import get_db_dep


router = APIRouter(prefix="/api", tags=["history"])


def _truncate(s: Optional[str], n: int = 120) -> Optional[str]:
    if not s:
        return s
    return s if len(s) <= n else s[: n - 1] + "\u2026"


def _last4(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = ''.join(ch for ch in phone if ch.isdigit())
    return digits[-4:] if digits else None


@router.get("/history")
async def get_history(
    source: str = Query("all"),
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[datetime] = Query(None, description="ISO8601 timestamp for keyset pagination"),
    conn=Depends(get_db_dep),
):
    if source not in ("all", "web_upload", "whatsapp"):
        raise HTTPException(status_code=400, detail="invalid source")

    # Normalize cursor to aware UTC if provided
    if cursor is not None and cursor.tzinfo is None:
        cursor = cursor.replace(tzinfo=timezone.utc)

    params: List[object] = []
    conds: List[str] = []

    if source != "all":
        params.append(source)
        conds.append(f"source = ${len(params)}")
    if cursor is not None:
        params.append(cursor)
        conds.append(f"created_at < ${len(params)}")

    where_sql = f" WHERE {' AND '.join(conds)}" if conds else ""
    order_sql = " ORDER BY created_at DESC, id DESC"
    params.append(limit)
    limit_sql = f" LIMIT ${len(params)}"

    sql = (
        "SELECT id, source, score, verdict, created_at, file_name, details_json, phone_number, correlation_id "
        "FROM analysis_results" + where_sql + order_sql + limit_sql
    )

    rows = await conn.fetch(sql, *params)

    items = []
    for r in rows:
        details = r.get("details_json") or {}
        msg_preview: Optional[str] = None
        if r["source"] == "whatsapp":
            if isinstance(details, dict):
                msg_preview = details.get("message") or details.get("text") or details.get("body")
            msg_preview = _truncate(msg_preview, 120)

        score_val = r["score"]
        if score_val is not None:
            try:
                score_val = float(score_val)
            except Exception:
                score_val = None

        created_at = r["created_at"]
        if isinstance(created_at, datetime):
            created_iso = created_at.isoformat()
        else:
            created_iso = str(created_at)

        items.append(
            {
                "id": int(r["id"]),
                "source": r["source"],
                "score": score_val,
                "verdict": r["verdict"],
                "created_at": created_iso,
                "file_name": r.get("file_name"),
                "message_preview": msg_preview,
                "phone_last4": _last4(r.get("phone_number")),
                "correlation_id": r.get("correlation_id"),
            }
        )

    return items

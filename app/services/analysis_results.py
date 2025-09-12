from typing import Literal, Optional, Dict, Any

from app.db import get_db  # expected to provide an async connection context


async def record_analysis_result(
    source: Literal['web_upload', 'whatsapp'],
    payload: Dict[str, Any],
    outcome: Dict[str, Any],
) -> int:
    """Insert a unified analysis result and return its id.

    Performs basic dedup when (source, correlation_id) is provided.
    Phone numbers are stored as-is (masking happens on read).
    """
    # Safe extraction
    score: Optional[float] = None
    raw_score = outcome.get('score') if isinstance(outcome, dict) else None
    try:
        if raw_score is not None:
            score = float(raw_score)
    except (TypeError, ValueError):
        score = None

    verdict: Optional[str] = None
    if isinstance(outcome, dict):
        verdict = outcome.get('verdict')

    # Prefer explicit details_json if present, otherwise fall back to outcome, then payload
    details_json: Dict[str, Any] = {}
    if isinstance(outcome, dict) and isinstance(outcome.get('details_json'), dict):
        details_json = outcome.get('details_json') or {}
    elif isinstance(payload, dict) and isinstance(payload.get('details_json'), dict):
        details_json = payload.get('details_json') or {}
    elif isinstance(outcome, dict):
        details_json = outcome
    elif isinstance(payload, dict):
        details_json = payload

    file_name: Optional[str] = None
    if isinstance(payload, dict):
        file_name = payload.get('file_name')

    message_sid: Optional[str] = None
    if isinstance(payload, dict):
        message_sid = payload.get('message_sid')

    phone_number: Optional[str] = None
    if isinstance(payload, dict):
        phone_number = payload.get('phone_number')

    user_id: Optional[str] = None
    if isinstance(payload, dict):
        user_id = payload.get('user_id')

    session_id: Optional[str] = None
    if isinstance(payload, dict):
        session_id = payload.get('session_id')

    correlation_id: Optional[str] = None
    # Allow correlation_id to come from payload or outcome
    if isinstance(payload, dict):
        correlation_id = payload.get('correlation_id')
    if not correlation_id and isinstance(outcome, dict):
        correlation_id = outcome.get('correlation_id')

    async with get_db() as conn:
        # Deduplication on (source, correlation_id) if provided
        if correlation_id:
            existing = await conn.fetchrow(
                """
                SELECT id FROM analysis_results
                WHERE source = $1 AND correlation_id = $2
                ORDER BY id DESC
                LIMIT 1
                """,
                source,
                correlation_id,
            )
            if existing:
                return int(existing['id'])

        row = await conn.fetchrow(
            """
            INSERT INTO analysis_results (
                source, score, verdict, details_json, file_name,
                message_sid, phone_number, user_id, session_id, correlation_id
            ) VALUES (
                $1, $2, $3, $4::jsonb, $5,
                $6, $7, $8, $9, $10
            )
            RETURNING id
            """,
            source,
            score,
            verdict,
            details_json or {},
            file_name,
            message_sid,
            phone_number,
            user_id,
            session_id,
            correlation_id,
        )

        return int(row['id'])


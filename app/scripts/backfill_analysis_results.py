import argparse
import asyncio
from typing import Any, Dict, List

from app.services.analysis_results import record_analysis_result


# Placeholder DAOs. Replace with real data access.
async def get_legacy_web_uploads() -> List[Dict[str, Any]]:
    return []


async def get_legacy_whatsapp_interactions() -> List[Dict[str, Any]]:
    return []


async def backfill(dry_run: bool = False) -> None:
    web = await get_legacy_web_uploads()
    wa = await get_legacy_whatsapp_interactions()

    inserted_web = 0
    inserted_wa = 0

    for row in web:
        payload: Dict[str, Any] = {
            "file_name": row.get("file_name"),
            "user_id": row.get("user_id"),
            "session_id": row.get("session_id"),
            "correlation_id": row.get("correlation_id"),
        }
        outcome: Dict[str, Any] = {
            "score": row.get("score"),
            "verdict": row.get("verdict"),
            "details_json": row.get("details_json") or {},
            "correlation_id": row.get("correlation_id"),
        }
        if not dry_run:
            await record_analysis_result("web_upload", payload, outcome)
        inserted_web += 1

    for row in wa:
        payload = {
            "message_sid": row.get("message_sid"),
            "phone_number": row.get("phone_number"),
            "user_id": row.get("user_id"),
            "session_id": row.get("session_id"),
            "correlation_id": row.get("correlation_id"),
            "details_json": row.get("details_json") or {},
        }
        outcome = {
            "score": row.get("score"),
            "verdict": row.get("verdict"),
            "details_json": row.get("details_json") or {},
            "correlation_id": row.get("correlation_id"),
        }
        if not dry_run:
            await record_analysis_result("whatsapp", payload, outcome)
        inserted_wa += 1

    print({"web_upload": inserted_web, "whatsapp": inserted_wa})


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill analysis_results from legacy sources")
    parser.add_argument("--dry-run", action="store_true", help="Do not write, only count")
    args = parser.parse_args()
    asyncio.run(backfill(dry_run=args.dry_run))


if __name__ == "__main__":
    main()


"""Library route — unified artifact browser grouped by conversation."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.auth import common_dependencies
from api.dependencies import AppState, get_app_state, get_db_session

router = APIRouter(prefix="/library", dependencies=common_dependencies)


@router.get("")
async def list_library(
    limit: int = 20,
    offset: int = 0,
    session: Any = Depends(get_db_session),
    state: AppState = Depends(get_app_state),
) -> dict:
    """Return artifacts grouped by conversation for the library page."""
    records, total = await state.db_repo.list_artifacts_grouped(
        session, limit=limit, offset=offset
    )
    return {
        "groups": [
            {
                "conversation_id": str(rec.conversation_id),
                "title": rec.conversation_title,
                "created_at": rec.conversation_created_at.isoformat(),
                "artifacts": [
                    {
                        "id": art.id,
                        "name": art.original_name,
                        "content_type": art.content_type,
                        "size": art.size,
                        "created_at": art.created_at.isoformat(),
                        "file_path": art.file_path,
                    }
                    for art in rec.artifacts
                ],
            }
            for rec in records
        ],
        "total": total,
    }

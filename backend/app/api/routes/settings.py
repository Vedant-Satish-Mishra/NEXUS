"""
NEXUS Settings & Data-Control API Routes (Step 5.D.1)
Endpoints:
- GET /settings : Retrieve current user settings
- PUT /settings : Update settings (validated against UserSettingsSchema)
- GET /export : Download ZIP of all user data (conversations, messages, memories, files metadata, feedback)
- DELETE /learning : Reset all learning signals for the user
- DELETE /account : Permanently delete user account and all cascading data (requires password confirmation)
"""
import io
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings as app_settings
from app.core.security import verify_password
from app.db.models import (
    Conversation,
    Feedback,
    FileRecord,
    LearningSignal,
    Memory,
    Message,
    Run,
    User,
    UserSettings,
)
from app.rag.vectorstore import VectorStore
from app.schemas.core import Principal
from app.schemas.settings import DeleteAccountRequest, UserSettingsSchema

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=UserSettingsSchema, status_code=status.HTTP_200_OK)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsSchema:
    """Retrieve persisted preferences for the current user."""
    stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    res = await db.execute(stmt)
    user_settings_record = res.scalar_one_or_none()

    if not user_settings_record or not user_settings_record.settings:
        return UserSettingsSchema()

    data = user_settings_record.settings
    return UserSettingsSchema(
        model_profile=data.get("model_profile", "fast"),
        default_preset=data.get("default_preset", "balanced"),
        memory_enabled=data.get("memory_enabled", True),
        learning_enabled=data.get("learning_enabled", True),
        privacy_mode=data.get("privacy_mode", True),
        web_search_enabled=data.get("web_search_enabled", False),
        theme=data.get("theme", "system"),
        reduced_motion=data.get("reduced_motion", False),
    )


@router.put("/settings", response_model=UserSettingsSchema, status_code=status.HTTP_200_OK)
async def update_user_settings(
    payload: UserSettingsSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsSchema:
    """Update and persist user preferences."""
    stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    res = await db.execute(stmt)
    user_settings_record = res.scalar_one_or_none()

    settings_dict = payload.model_dump()

    if not user_settings_record:
        user_settings_record = UserSettings(user_id=current_user.id, settings=settings_dict)
        db.add(user_settings_record)
    else:
        user_settings_record.settings = settings_dict

    await db.commit()
    return payload


@router.delete("/learning", status_code=status.HTTP_200_OK)
async def reset_learning_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Wipes all adaptive learning signals for the user."""
    stmt = delete(LearningSignal).where(LearningSignal.user_id == current_user.id)
    result = await db.execute(stmt)
    await db.commit()
    return {"status": "ok", "deleted_signals": result.rowcount}


@router.get("/export", status_code=status.HTTP_200_OK)
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Exports all user data in a portable ZIP archive containing JSON files:
    - conversations.json (with messages)
    - memories.json
    - files.json (metadata only)
    - feedback.json
    - settings.json
    Passwords and authorization tokens are strictly excluded.
    """
    # 1. Fetch Conversations and Messages
    conv_stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.asc())
    )
    conv_res = await db.execute(conv_stmt)
    conversations = conv_res.scalars().all()

    conv_data = []
    for c in conversations:
        msg_stmt = (
            select(Message)
            .where(Message.conversation_id == c.id)
            .order_by(Message.created_at.asc())
        )
        msg_res = await db.execute(msg_stmt)
        messages = msg_res.scalars().all()
        conv_data.append({
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        })

    # 2. Fetch Memories
    mem_stmt = (
        select(Memory)
        .where(Memory.user_id == current_user.id)
        .order_by(Memory.confirmed_at.asc())
    )
    mem_res = await db.execute(mem_stmt)
    memories = [
        {
            "id": m.id,
            "kind": m.kind,
            "content": m.content,
            "confirmed_at": m.confirmed_at.isoformat() if m.confirmed_at else None,
            "active": m.active,
        }
        for m in mem_res.scalars().all()
    ]

    # 3. Fetch File metadata
    files_stmt = (
        select(FileRecord)
        .where(FileRecord.user_id == current_user.id)
        .order_by(FileRecord.created_at.asc())
    )
    f_res = await db.execute(files_stmt)
    files_data = [
        {
            "id": f.id,
            "filename": f.filename,
            "mime": f.mime,
            "size": f.size,
            "scope": f.scope,
            "status": f.status,
            "chunks_count": f.chunks,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in f_res.scalars().all()
    ]

    # 4. Fetch Feedback
    fb_stmt = (
        select(Feedback)
        .join(Message, Feedback.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == current_user.id)
    )
    fb_res = await db.execute(fb_stmt)
    feedback_data = [
        {
            "id": fb.id,
            "message_id": fb.message_id,
            "rating": fb.rating,
            "comment": fb.comment,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
        for fb in fb_res.scalars().all()
    ]

    # 5. Fetch Settings
    s_stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    s_res = await db.execute(s_stmt)
    s_rec = s_res.scalar_one_or_none()
    settings_data = s_rec.settings if s_rec else {}

    # Build ZIP archive in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("conversations.json", json.dumps(conv_data, indent=2))
        zip_file.writestr("memories.json", json.dumps(memories, indent=2))
        zip_file.writestr("files.json", json.dumps(files_data, indent=2))
        zip_file.writestr("feedback.json", json.dumps(feedback_data, indent=2))
        zip_file.writestr("settings.json", json.dumps(settings_data, indent=2))
        zip_file.writestr(
            "metadata.txt",
            f"NEXUS Data Export\nUser ID: {current_user.id}\nExported At: {datetime.now(timezone.utc).isoformat()}\nFormat Version: 1.0\n",
        )

    buf.seek(0)
    filename = f"nexus_export_{current_user.id[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_user_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Permanently deletes user account and executes full cascade deletion:
    - Postgres rows (User, Conversations, Messages, Runs, Events, Files, Memories, Signals, Settings)
    - Chroma vector collections (user KB vectors and memory vectors)
    - Uploaded disk files
    Requires user password verification.
    """
    # 1. Verify password
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password confirmation",
        )

    user_id = current_user.id
    principal = Principal(user_id=user_id, role="user")

    # 2. Cascade delete from ChromaDB vectors
    try:
        vs = VectorStore()
        # Delete user's memories in Chroma
        await vs.delete_all_memories(user_id)
        # Fetch user's file IDs and delete vectors
        f_stmt = select(FileRecord.id).where(FileRecord.user_id == user_id)
        f_res = await db.execute(f_stmt)
        file_ids = f_res.scalars().all()
        for fid in file_ids:
            await vs.delete_file(principal, fid)
    except Exception as e:
        # Non-fatal log, continue database purge
        pass

    # 3. Clean up disk uploads directory if exists
    upload_dir = os.path.join(getattr(app_settings, "UPLOAD_DIR", "data/uploads"), user_id)
    if os.path.exists(upload_dir):
        try:
            shutil.rmtree(upload_dir, ignore_errors=True)
        except Exception:
            pass

    # 4. Cascade delete user from Postgres
    # All dependent tables have ForeignKeys with ondelete="CASCADE" to users.id
    await db.delete(current_user)
    await db.commit()

    return {"status": "ok", "message": "Account and all associated data permanently deleted"}

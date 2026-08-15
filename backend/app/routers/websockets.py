from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dependencies import AuthenticatedUser
from app.events import EventSubscription, event_envelope
from app.models import Staff, User
from app.schemas import UserRole
from app.security import TokenError, decode_token


router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])


def websocket_user(websocket: WebSocket, token: str) -> AuthenticatedUser | None:
    try:
        payload = decode_token(token, websocket.app.state.jwt_secret, "access")
        role = UserRole(payload["role"])
    except (TokenError, ValueError):
        return None
    with websocket.app.state.database.session_factory() as db:
        user = db.get(User, payload["sub"])
        if (
            user is None
            or not user.is_active
            or user.role != role.value
            or payload.get("ver", 0) != user.auth_version
        ):
            return None
        staff = db.get(Staff, user.id) if role is UserRole.STAFF else None
        return AuthenticatedUser(
            id=user.id,
            role=role,
            display_name=user.display_name,
            store_id=staff.store_id if staff else None,
        )


async def stream_topic(websocket: WebSocket, topic: str) -> None:
    broker = websocket.app.state.event_broker
    subscription: EventSubscription = broker.subscribe(topic)
    await websocket.accept()
    receiver = asyncio.create_task(websocket.receive_json())
    event_receiver = asyncio.create_task(subscription.queue.get())
    try:
        while True:
            done, _ = await asyncio.wait(
                {receiver, event_receiver},
                timeout=30,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if not done:
                await websocket.send_json(event_envelope("PING", {}))
                continue
            if event_receiver in done:
                await websocket.send_json(event_receiver.result())
                event_receiver = asyncio.create_task(subscription.queue.get())
            if receiver in done:
                message = receiver.result()
                if isinstance(message, dict) and message.get("event") == "PING":
                    await websocket.send_json(event_envelope("PONG", {}))
                receiver = asyncio.create_task(websocket.receive_json())
    except (WebSocketDisconnect, RuntimeError, ValueError):
        pass
    finally:
        broker.unsubscribe(subscription)
        receiver.cancel()
        event_receiver.cancel()
        with suppress(asyncio.CancelledError, WebSocketDisconnect):
            await receiver
        with suppress(asyncio.CancelledError):
            await event_receiver


@router.websocket("/staff/stores/{store_id}")
async def staff_events(websocket: WebSocket, store_id: str, token: str) -> None:
    user = websocket_user(websocket, token)
    if user is None:
        await websocket.close(code=4401, reason="유효한 Access Token이 필요합니다.")
        return
    if user.role is not UserRole.STAFF or user.store_id != store_id:
        await websocket.close(code=4403, reason="소속 매장의 이벤트만 구독할 수 있습니다.")
        return
    await stream_topic(websocket, f"staff:{store_id}")


@router.websocket("/customers/me")
async def customer_events(websocket: WebSocket, token: str) -> None:
    user = websocket_user(websocket, token)
    if user is None:
        await websocket.close(code=4401, reason="유효한 Access Token이 필요합니다.")
        return
    if user.role is not UserRole.CUSTOMER:
        await websocket.close(code=4403, reason="고객 권한이 필요합니다.")
        return
    await stream_topic(websocket, f"customer:{user.id}")

"""
Messaging Service - Microservice
 Handles real-time messaging between users
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import json
import jwt
from collections import defaultdict

app = FastAPI(title="Messaging Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Models ============

class Message(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    created_at: datetime = datetime.utcnow()


class Conversation(BaseModel):
    id: str
    member1_id: str
    member2_id: str
    listing_id: Optional[str] = None
    order_id: Optional[str] = None
    last_message: Optional[Message] = None
    created_at: datetime = datetime.utcnow()


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
    
    async def send_personal(self, message: dict, user_id: str):
        for connection in self.active_connections.get(user_id, []):
            await connection.send_json(message)
    
    async def broadcast(self, message: dict, room: str):
        # For group chats
        pass


manager = ConnectionManager()


# ============ In-Memory Storage (Use Redis in production) ============

conversations: dict[str, Conversation] = {}
messages: dict[str, List[Message]] = defaultdict(list)


# ============ WebSocket Endpoint ============

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket for real-time messaging"""
    try:
        # Verify token
        from app.core.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                msg_type = message_data.get("type")
                
                if msg_type == "message":
                    await handle_message(user_id, message_data)
                elif msg_type == "typing":
                    await handle_typing(user_id, message_data)
                elif msg_type == "read":
                    await handle_read(user_id, message_data)
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            
    except Exception as e:
        await websocket.close(code=4001, reason=str(e))


async def handle_message(sender_id: str, data: dict):
    """Handle sending a message"""
    conversation_id = data.get("conversation_id")
    content = data.get("content")
    
    # Create message
    message = Message(
        id=f"msg_{datetime.utcnow().timestamp()}",
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content
    )
    
    messages[conversation_id].append(message)
    
    # Get conversation to find recipient
    conv = conversations.get(conversation_id)
    if conv:
        recipient_id = conv.member2_id if conv.member1_id == sender_id else conv.member1_id
        
        # Send to recipient
        await manager.send_personal({
            "type": "message",
            "data": message.dict()
        }, recipient_id)
        
        # Send to sender (acknowledgment)
        await manager.send_personal({
            "type": "acknowledged",
            "message_id": message.id
        }, sender_id)


async def handle_typing(sender_id: str, data: dict):
    """Handle typing indicator"""
    conversation_id = data.get("conversation_id")
    conv = conversations.get(conversation_id)
    
    if conv:
        recipient_id = conv.member2_id if conv.member1_id == sender_id else conv.member1_id
        await manager.send_personal({
            "type": "typing",
            "sender_id": sender_id,
            "conversation_id": conversation_id
        }, recipient_id)


async def handle_read(sender_id: str, data: dict):
    """Handle read receipt"""
    conversation_id = data.get("conversation_id")
    
    # Mark messages as read
    for msg in messages[conversation_id]:
        if msg.sender_id != sender_id:
            # In production, update database
            pass
    
    # Notify sender
    conv = conversations.get(conversation_id)
    if conv:
        recipient_id = conv.member2_id if conv.member1_id == sender_id else conv.member1_id
        await manager.send_personal({
            "type": "read",
            "conversation_id": conversation_id,
            "read_by": sender_id
        }, recipient_id)


# ============ REST Endpoints ============

@app.get("/health")
def health():
    return {"status": "healthy", "service": "messaging"}


@app.post("/conversations", response_model=Conversation)
def create_conversation(
    member1_id: str,
    member2_id: str,
    listing_id: str = None,
    order_id: str = None
):
    """Create or get existing conversation"""
    # Check if exists
    for conv in conversations.values():
        if (conv.member1_id == member1_id and conv.member2_id == member2_id) or \
           (conv.member1_id == member2_id and conv.member2_id == member1_id):
            return conv
    
    # Create new
    conv = Conversation(
        id=f"conv_{datetime.utcnow().timestamp()}",
        member1_id=member1_id,
        member2_id=member2_id,
        listing_id=listing_id,
        order_id=order_id
    )
    conversations[conv.id] = conv
    return conv


@app.get("/conversations/{user_id}")
def get_user_conversations(user_id: str):
    """Get all conversations for a user"""
    user_convs = [
        conv for conv in conversations.values()
        if conv.member1_id == user_id or conv.member2_id == user_id
    ]
    return user_convs


@app.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: str, limit: int = 50):
    """Get messages in a conversation"""
    return messages.get(conversation_id, [])[-limit:]


@app.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, sender_id: str = None, content: str = None):
    """Send a message (REST alternative to WebSocket)"""
    message = Message(
        id=f"msg_{datetime.utcnow().timestamp()}",
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content
    )
    messages[conversation_id].append(message)
    
    # Get recipient and send notification
    conv = conversations.get(conversation_id)
    if conv:
        recipient_id = conv.member2_id if conv.member1_id == sender_id else conv.member1_id
        asyncio.create_task(manager.send_personal({
            "type": "message",
            "data": message.dict()
        }, recipient_id))
    
    return message


@app.get("/unread/{user_id}")
def get_unread_count(user_id: str):
    """Get unread message count for user"""
    total = 0
    for conv_id, msgs in messages.items():
        conv = conversations.get(conv_id)
        if conv and (conv.member1_id == user_id or conv.member2_id == user_id):
            # Count unread (in production, track read status in DB)
            total += len(msgs)
    return {"unread": total}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

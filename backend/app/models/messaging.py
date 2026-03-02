"""
Messaging System - Buyer/Seller Chat
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: f"conv_{func.random(16)}")
    
    # Participants
    member1_id = Column(String, ForeignKey("members.id"), nullable=False)
    member2_id = Column(String, ForeignKey("members.id"), nullable=False)
    
    # Related to (optional)
    listing_id = Column(String, ForeignKey("marketplace_listings.id"))
    order_id = Column(String, ForeignKey("marketplace_orders.id"))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: f"msg_{func.random(16)}")
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(String, ForeignKey("members.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class MessageAttachment(Base):
    __tablename__ = "message_attachments"
    
    id = Column(String, primary_key=True, default=lambda: f"matt_{func.random(16)}")
    
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String)
    file_name = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())

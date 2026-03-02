"""
Notifications Service Interface
Future microservice: notifications-service
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import requests


class NotificationChannel:
    """Notification delivery channels"""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"


class NotificationService:
    """Unified notification operations"""
    
    @staticmethod
    def send(db: Session, user_id: str, title: str, body: str, channel: str = NotificationChannel.IN_APP, **kwargs):
        """Send notification via specified channel"""
        if channel == NotificationChannel.PUSH:
            return NotificationService._send_push(user_id, title, body, **kwargs)
        elif channel == NotificationChannel.SMS:
            return NotificationService._send_sms(user_id, title, body, **kwargs)
        elif channel == NotificationChannel.EMAIL:
            return NotificationService._send_email(user_id, title, body, **kwargs)
        else:
            return NotificationService._send_in_app(db, user_id, title, body, **kwargs)
    
    @staticmethod
    def _send_push(user_id: str, title: str, body: str, **kwargs):
        """Send push notification"""
        # Would integrate with Expo FCM
        return {"status": "SENT", "channel": "push"}
    
    @staticmethod
    def _send_sms(user_id: str, title: str, body: str, phone: str = None, **kwargs):
        """Send SMS"""
        # Would use Africa's Talking
        return {"status": "SENT", "channel": "sms"}
    
    @staticmethod
    def _send_email(user_id: str, title: str, body: str, email: str = None, **kwargs):
        """Send email"""
        # Would use SMTP/SendGrid
        return {"status": "SENT", "channel": "email"}
    
    @staticmethod
    def _send_in_app(db: Session, user_id: str, title: str, body: str, **kwargs):
        """Save in-app notification"""
        from app.models import Notification, NotificationType, NotificationChannel as NC
        
        notif = Notification(
            user_id=user_id,
            title=title,
            message=body,
            type=NotificationType.GENERAL,
            channel=NC.IN_APP,
            is_read=False
        )
        db.add(notif)
        db.commit()
        
        return {"status": "SENT", "channel": "in_app"}


class TransactionalNotifications:
    """Business-specific notification templates"""
    
    @staticmethod
    def notify_kudos(db: Session, from_member: str, to_member: str, message: str):
        """Notify member received kudos"""
        from app.models import Member
        
        recipient = db.query(Member).filter(Member.id == to_member).first()
        if not recipient:
            return
        
        title = "You received Kudos! 🎉"
        body = f"{from_member} recognized you: {message}"
        
        # Send to all channels
        NotificationService.send(db, to_member, title, body, NotificationChannel.PUSH)
        if recipient.phone:
            NotificationService.send(db, to_member, title, body, NotificationChannel.SMS, phone=recipient.phone)
    
    @staticmethod
    def notify_task_assigned(db: Session, member_id: str, task_title: str, due_date: str):
        """Notify member assigned to task"""
        title = "New Task Assigned"
        body = f"You've been assigned: {task_title}. Due: {due_date}"
        NotificationService.send(db, member_id, title, body, NotificationChannel.PUSH)
    
    @staticmethod
    def notify_task_status(db: Session, member_id: str, task_title: str, old_status: str, new_status: str):
        """Notify member of task status change"""
        title = "Task Status Updated"
        body = f"'{task_title}' changed from {old_status} to {new_status}"
        NotificationService.send(db, member_id, title, body, NotificationChannel.PUSH)
    
    @staticmethod
    def notify_marketplace_order(db: Session, member_id: str, order_id: str, status: str):
        """Notify marketplace order updates"""
        messages = {
            "PAID": "Payment received. Order is being processed.",
            "SHIPPED": f"Your order {order_id} has been shipped.",
            "DELIVERED": f"Order {order_id} delivered. Confirm to release funds.",
            "COMPLETED": f"Order {order_id} completed. Funds released to seller."
        }
        
        title = "Order Update"
        body = messages.get(status, f"Order {order_id} status: {status}")
        NotificationService.send(db, member_id, title, body, NotificationChannel.PUSH)
    
    @staticmethod
    def notify_payment_received(db: Session, member_id: str, amount: float, source: str):
        """Notify payment received"""
        title = "Payment Received"
        body = f"You received KES {amount} from {source}"
        NotificationService.send(db, member_id, title, body, NotificationChannel.PUSH)
    
    @staticmethod
    def notify_loan_approved(db: Session, member_id: str, loan_id: str, amount: float):
        """Notify loan approved"""
        title = "Loan Approved! 💰"
        body = f"Your loan request for KES {amount} has been approved."
        NotificationService.send(db, member_id, title, body, NotificationChannel.PUSH)
    
    @staticmethod
    def notify_proposal_vote(db: Session, member_id: str, proposal_title: str, vote_count: int):
        """Notify proposal vote results"""
        title = "Proposal Vote Update"
        body = f"'{proposal_title}' has {vote_count} votes"
        NotificationService.send(db, member_id, title, body, NotificationChannel.PUSH)


class BatchNotificationService:
    """Batch notification operations"""
    
    @staticmethod
    def notify_all_members(db: Session, org_id: str, title: str, body: str, channel: str = NotificationChannel.IN_APP):
        """Send notification to all org members"""
        from app.models import Member
        
        members = db.query(Member).filter(Member.organization_id == org_id).all()
        
        results = []
        for member in members:
            result = NotificationService.send(db, member.id, title, body, channel)
            results.append({"member_id": member.id, "result": result})
        
        return {"sent": len(results), "results": results}
    
    @staticmethod
    def notify_role(db: Session, org_id: str, role: str, title: str, body: str):
        """Send notification to members with specific role"""
        from app.models import Member
        
        members = db.query(Member).filter(
            Member.organization_id == org_id,
            Member.role == role
        ).all()
        
        results = []
        for member in members:
            result = NotificationService.send(db, member.id, title, body, NotificationChannel.PUSH)
            results.append({"member_id": member.id, "result": result})
        
        return {"sent": len(results), "results": results}


__all__ = [
    "NotificationChannel",
    "NotificationService",
    "TransactionalNotifications",
    "BatchNotificationService"
]

"""
Notifications Service
Microservice for Push, SMS, Email, In-App notifications
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import jwt

app = FastAPI(title="Notifications Service")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ============ Pydantic Models ============

class NotificationRequest(BaseModel):
    user_id: str
    title: str
    body: str
    channel: str = "in_app"  # push, sms, email, in_app


class BatchNotificationRequest(BaseModel):
    user_ids: List[str]
    title: str
    body: str
    channel: str = "in_app"


class PushTokenRequest(BaseModel):
    user_id: str
    token: str
    platform: str = "android"  # android, ios


# ============ In-Memory Storage ============

# Push tokens: user_id -> [tokens]
push_tokens = {}

# Notifications: user_id -> [notifications]
notifications = {}


# ============ Helpers ============

def get_current_member(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return {"id": payload.get("sub")}
    except:
        raise HTTPException(status_code=401)


# ============ Health ============

@app.get("/health")
def health():
    return {"status": "healthy", "service": "notifications"}


# ============ Push Notifications ============

@app.post("/push/register")
def register_push_token(request: PushTokenRequest):
    """Register push token for user"""
    if request.user_id not in push_tokens:
        push_tokens[request.user_id] = []
    
    token_entry = {"token": request.token, "platform": request.platform, "created_at": datetime.utcnow().isoformat()}
    
    # Avoid duplicates
    existing = [t for t in push_tokens[request.user_id] if t["token"] != request.token]
    existing.append(token_entry)
    push_tokens[request.user_id] = existing
    
    return {"status": "registered", "token_count": len(push_tokens[request.user_id])}


@app.post("/push/send")
def send_push_notification(request: NotificationRequest):
    """Send push notification to user"""
    tokens = push_tokens.get(request.user_id, [])
    
    if not tokens:
        return {"status": "no_tokens", "sent": 0}
    
    # In production: Send to FCM/APNS
    # For now, simulate
    
    sent = 0
    for token in tokens:
        # Simulate sending
        sent += 1
    
    return {"status": "sent", "sent_to": sent, "title": request.title}


# ============ SMS Notifications ============

@app.post("/sms/send")
def send_sms(request: NotificationRequest):
    """Send SMS notification"""
    # In production: Use Africa's Talking
    
    # Simulate
    return {
        "status": "sent",
        "to": request.user_id,  # Would resolve to phone
        "message": request.body
    }


# ============ Email Notifications ============

@app.post("/email/send")
def send_email(request: NotificationRequest):
    """Send email notification"""
    # In production: Use SMTP/SendGrid
    
    return {
        "status": "sent",
        "to": request.user_id,  # Would resolve to email
        "subject": request.title,
        "body": request.body
    }


# ============ In-App Notifications ============

@app.post("/in-app/send")
def send_in_app_notification(request: NotificationRequest):
    """Send in-app notification"""
    if request.user_id not in notifications:
        notifications[request.user_id] = []
    
    notif = {
        "id": f"notif_{datetime.utcnow().timestamp()}",
        "title": request.title,
        "body": request.body,
        "created_at": datetime.utcnow().isoformat(),
        "read": False
    }
    
    notifications[request.user_id].append(notif)
    
    return {"status": "sent", "notification_id": notif["id"]}


@app.get("/in-app/{user_id}")
def get_notifications(user_id: str, unread_only: bool = False):
    """Get user's notifications"""
    user_notifs = notifications.get(user_id, [])
    
    if unread_only:
        user_notifs = [n for n in user_notifs if not n.get("read")]
    
    return user_notifs


@app.post("/in-app/{user_id}/{notification_id}/read")
def mark_notification_read(user_id: str, notification_id: str):
    """Mark notification as read"""
    user_notifs = notifications.get(user_id, [])
    
    for notif in user_notifs:
        if notif["id"] == notification_id:
            notif["read"] = True
            notif["read_at"] = datetime.utcnow().isoformat()
            return {"status": "marked_read"}
    
    raise HTTPException(status_code=404, detail="Notification not found")


# ============ Unified Send ============

@app.post("/send")
def send_notification(request: NotificationRequest):
    """Send notification via specified channel"""
    if request.channel == "push":
        return send_push_notification(request)
    elif request.channel == "sms":
        return send_sms(request)
    elif request.channel == "email":
        return send_email(request)
    else:
        return send_in_app_notification(request)


# ============ Batch Notifications ============

@app.post("/batch")
def send_batch_notifications(request: BatchNotificationRequest):
    """Send notification to multiple users"""
    results = []
    
    for user_id in request.user_ids:
        result = send_notification(NotificationRequest(
            user_id=user_id,
            title=request.title,
            body=request.body,
            channel=request.channel
        ))
        results.append({"user_id": user_id, "result": result})
    
    return {"sent": len(results), "results": results}


# ============ Transactional Notifications ============

@app.post("/transactional/kudos")
def notify_kudos(to_member: str, from_member: str, message: str):
    """Notify member received kudos"""
    return send_in_app_notification(NotificationRequest(
        user_id=to_member,
        title="You received Kudos! 🎉",
        body=f"{from_member} recognized you: {message}"
    ))


@app.post("/transactional/task-assigned")
def notify_task_assigned(member_id: str, task_title: str, due_date: str):
    """Notify task assignment"""
    return send_in_app_notification(NotificationRequest(
        user_id=member_id,
        title="New Task Assigned",
        body=f"You've been assigned: {task_title}. Due: {due_date}"
    ))


@app.post("/transactional/order-status")
def notify_order_status(member_id: str, order_id: str, status: str):
    """Notify order status change"""
    messages = {
        "PAID": "Payment received. Order being processed.",
        "SHIPPED": f"Order {order_id} has been shipped.",
        "DELIVERED": f"Order {order_id} delivered. Confirm to release funds.",
        "COMPLETED": f"Order {order_id} completed."
    }
    
    return send_in_app_notification(NotificationRequest(
        user_id=member_id,
        title="Order Update",
        body=messages.get(status, f"Order {order_id}: {status}")
    ))


@app.post("/transactional/loan-approved")
def notify_loan_approved(member_id: str, amount: float):
    """Notify loan approved"""
    return send_in_app_notification(NotificationRequest(
        user_id=member_id,
        title="Loan Approved! 💰",
        body=f"Your loan for KES {amount} has been approved."
    ))


@app.post("/transactional/payment-received")
def notify_payment_received(member_id: str, amount: float, source: str):
    """Notify payment received"""
    return send_in_app_notification(NotificationRequest(
        user_id=member_id,
        title="Payment Received",
        body=f"You received KES {amount} from {source}"
    ))


# ============ Templates ============

templates = {
    "welcome": {
        "title": "Welcome to Chama!",
        "body": "Your chama account is ready. Start contributing!"
    },
    "contribution_reminder": {
        "title": "Contribution Reminder",
        "body": "Your monthly contribution is due. Keep your chama strong!"
    },
    "meeting_notice": {
        "title": "Upcoming Meeting",
        "body": "Chama meeting scheduled. Check your calendar for details."
    }
}


@app.get("/templates")
def list_templates():
    """List notification templates"""
    return templates


@app.post("/templates/{template_id}/send")
def send_template(template_id: str, user_id: str):
    """Send templated notification"""
    if template_id not in templates:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = templates[template_id]
    return send_in_app_notification(NotificationRequest(
        user_id=user_id,
        title=template["title"],
        body=template["body"]
    ))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

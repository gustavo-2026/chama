"""
Payments Service
Microservice for M-Pesa, Pesapal, Wallet, Escrow
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import requests
import base64
import os
import jwt
import uuid

app = FastAPI(title="Payments Service")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "123456")
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_ENV = os.getenv("MPESA_ENV", "sandbox")


# ============ Pydantic Models ============

class PaymentRequest(BaseModel):
    amount: float
    phone: str
    reference: str
    description: str = "Payment"


class B2CRequest(BaseModel):
    phone: str
    amount: float
    remarks: str = "Withdrawal"


class WalletPaymentRequest(BaseModel):
    amount: float
    member_id: str


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


def get_mpesa_token():
    """Get M-Pesa OAuth token"""
    if not MPESA_CONSUMER_KEY:
        raise HTTPException(status_code=503, detail="M-Pesa not configured")
    
    url = f"https://{'sandbox' if MPESA_ENV == 'sandbox' else 'api'}.safaricom.co.ke/oauth/v1/generate"
    response = requests.get(url, params={"grant_type": "client_credentials"}, 
                          auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET), timeout=30)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    raise HTTPException(status_code=500, detail="Failed to get M-Pesa token")


# ============ Health ============

@app.get("/health")
def health():
    return {"status": "healthy", "service": "payments"}


# ============ M-Pesa STK Push ============

@app.post("/mpesa/stk-push")
def initiate_stk_push(request: PaymentRequest):
    """Initiate M-Pesa STK Push"""
    if not MPESA_CONSUMER_KEY:
        return {"success": False, "error": "M-Pesa not configured"}
    
    # Format phone
    phone = request.phone
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone
    
    try:
        token = get_mpesa_token()
        
        # Generate password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
        encoded_password = base64.b64encode(password.encode()).decode()
        
        # STK Push request
        url = f"https://{'sandbox' if MPESA_ENV == 'sandbox' else 'api'}.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": encoded_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerBuyGoodsOnline",
            "Amount": int(request.amount),
            "PartyA": phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": os.getenv("MPESA_CALLBACK_URL", "https://your-domain.com/callback"),
            "AccountReference": request.reference,
            "TransactionDesc": request.description
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "checkout_request_id": result.get("CheckoutRequestID"),
                "message": "STK push sent"
            }
        return {"success": False, "error": response.text}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/mpesa/callback")
def mpesa_callback(Body: dict):
    """Handle M-Pesa callback"""
    try:
        callback = Body.get("stkCallback", {})
        result_code = callback.get("ResultCode")
        
        if result_code == 0:
            # Payment successful
            metadata = callback.get("CallbackMetadata", {})
            receipt = None
            amount = None
            
            for item in metadata.get("Item", []):
                if item.get("Name") == "MpesaReceiptNumber":
                    receipt = item.get("Value")
                elif item.get("Name") == "Amount":
                    amount = item.get("Value")
            
            # In production: Update order status, release escrow
            return {"status": "success", "receipt": receipt, "amount": amount}
        
        return {"status": "failed", "code": result_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/mpesa/b2c")
def initiate_b2c(request: B2CRequest):
    """Disburse funds to member (B2C)"""
    if not MPESA_CONSUMER_KEY:
        return {"success": False, "error": "M-Pesa not configured"}
    
    phone = request.phone
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone
    
    try:
        token = get_mpesa_token()
        
        url = f"https://{'sandbox' if MPESA_ENV == 'sandbox' else 'api'}.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        payload = {
            "InitiatorName": os.getenv("MPESA_INITIATOR", "testapi"),
            "SecurityCredential": os.getenv("MPESA_B2C_SECURITY", "test"),
            "CommandID": "BusinessPayment",
            "Amount": int(request.amount),
            "PartyA": MPESA_SHORTCODE,
            "PartyB": phone,
            "Remarks": request.remarks,
            "QueueTimeOutURL": f"{os.getenv('MPESA_CALLBACK_URL')}/timeout",
            "ResultURL": f"{os.getenv('MPESA_CALLBACK_URL')}/b2c-result"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {"success": True, "conversation_id": result.get("ConversationID")}
        
        return {"success": False, "error": response.text}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ Pesapal ============

PESAPAL_KEY = os.getenv("PESAPAL_CONSUMER_KEY")
PESAPAL_SECRET = os.getenv("PESAPAL_CONSUMER_SECRET")


@app.post("/pesapal/order")
def create_pesapal_order(request: PaymentRequest):
    """Create Pesapal payment order"""
    if not PESAPAL_KEY:
        return {"success": False, "error": "Pesapal not configured"}
    
    order_id = f"pes_{uuid.uuid4().hex[:12]}"
    
    return {
        "success": True,
        "order_id": order_id,
        "message": "Redirect to Pesapal"
    }


# ============ Wallet ============

# In-memory wallet (use database in production)
wallets = {}


@app.get("/wallet/{member_id}")
def get_wallet(member_id: str):
    if member_id not in wallets:
        wallets[member_id] = {"balance": 0, "reserved": 0}
    return wallets[member_id]


@app.post("/wallet/deposit")
def wallet_deposit(request: WalletPaymentRequest):
    """Deposit to wallet"""
    if request.member_id not in wallets:
        wallets[request.member_id] = {"balance": 0, "reserved": 0}
    
    wallets[request.member_id]["balance"] += request.amount
    return {"status": "success", "balance": wallets[request.member_id]["balance"]}


@app.post("/wallet/withdraw")
def wallet_withdraw(request: WalletPaymentRequest):
    """Withdraw from wallet"""
    if request.member_id not in wallets:
        raise HTTPException(status_code=400, detail="No wallet")
    
    wallet = wallets[request.member_id]
    available = wallet["balance"] - wallet["reserved"]
    
    if available < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    wallet["balance"] -= request.amount
    return {"status": "success", "balance": wallet["balance"]}


@app.post("/wallet/pay")
def wallet_pay(request: WalletPaymentRequest):
    """Pay from wallet"""
    if request.member_id not in wallets:
        raise HTTPException(status_code=400, detail="No wallet")
    
    wallet = wallets[request.member_id]
    available = wallet["balance"] - wallet["reserved"]
    
    if available < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Reserve and deduct
    wallet["balance"] -= request.amount
    return {"status": "success", "balance": wallet["balance"]}


# ============ Escrow ============

escrow_account = {"balance": 0}


@app.post("/escrow/hold")
def hold_escrow(amount: float, order_id: str):
    """Hold funds in escrow"""
    escrow_account["balance"] += amount
    return {"status": "held", "order_id": order_id, "amount": amount}


@app.post("/escrow/release")
def release_escrow(order_id: str, member_id: str):
    """Release escrow to seller"""
    # In production: Transfer to seller's wallet or B2C
    return {"status": "released", "order_id": order_id, "to": member_id}


@app.post("/escrow/refund")
def refund_escrow(order_id: str):
    """Refund buyer"""
    return {"status": "refunded", "order_id": order_id}


# ============ Payment Providers ============

@app.get("/providers")
def get_providers():
    """List available payment providers"""
    providers = []
    
    if MPESA_CONSUMER_KEY:
        providers.append({"id": "mpesa", "name": "M-Pesa", "type": "mobile_money"})
    
    if PESAPAL_KEY:
        providers.append({"id": "pesapal", "name": "Pesapal", "type": "card_bank"})
    
    providers.append({"id": "wallet", "name": "Wallet", "type": "balance"})
    
    return providers


@app.post("/checkout")
def unified_checkout(provider: str, amount: float, reference: str, phone: str = None):
    """Unified checkout"""
    if provider == "mpesa":
        return initiate_stk_push(PaymentRequest(amount=amount, phone=phone, reference=reference, description="Payment"))
    elif provider == "pesapal":
        return create_pesapal_order(PaymentRequest(amount=amount, phone=phone, reference=reference, description="Payment"))
    elif provider == "wallet":
        return {"provider": "wallet", "status": "use_wallet_endpoint"}
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

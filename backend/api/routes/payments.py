"""
Payment and Subscription API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import hmac
import uuid

from backend.models.muse_api import (
    PaymentCreateRequest, PaymentResponse, PaymentCallbackRequest,
    SubscriptionResponse, PlanResponse, SuccessResponse
)
from backend.models.muse import Plan, Subscription, PaymentTransaction
from backend.core.database import get_db
from backend.core.caching import cache_manager
from loguru import logger

router = APIRouter(prefix="/v1/payments", tags=["payments"])

# PhonePe configuration (simplified for demo)
PHONEPE_MERCHANT_ID = "MERCHANTUAT"
PHONEPE_SALT_KEY = "salt_key_placeholder"
PHONEPE_API_URL = "https://api.phonepe.com/apis/hermes"

# Dependency to get workspace context
async def get_workspace_context() -> str:
    """Get current workspace ID - in production from JWT/auth"""
    return "default_workspace"


# Payment Endpoints
@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    request: PaymentCreateRequest,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_context)
):
    """
    Create a new payment session with PhonePe
    """
    try:
        # Validate plan
        plan = db.query(Plan).filter(
            and_(
                Plan.plan_id == request.plan_id,
                Plan.is_active == True
            )
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Validate amount matches plan price
        if abs(request.amount - plan.price) > 0.01:  # Small tolerance for floating point
            raise HTTPException(
                status_code=400,
                detail=f"Amount {request.amount} does not match plan price {plan.price}"
            )
        
        # Generate order ID
        order_id = str(uuid.uuid4())
        
        # Create payment transaction record
        transaction = PaymentTransaction(
            workspace_id=workspace_id,
            payment_provider="phonepe",
            order_id=order_id,
            transaction_id="",  # Will be filled after PhonePe response
            amount=request.amount,
            currency=request.currency,
            status="pending"
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # In production, this would make actual PhonePe API call
        # For demo, we'll simulate the response
        payment_url = f"https://api.phonepe.com/pay/{order_id}"
        
        # Update transaction with PhonePe transaction ID
        transaction.transaction_id = f"TXN_{order_id}"
        db.commit()
        
        return PaymentResponse(
            success=True,
            payment_url=payment_url,
            order_id=order_id,
            amount=request.amount,
            currency=request.currency,
            message="Payment session created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback", response_model=SuccessResponse)
async def payment_callback(
    request: PaymentCallbackRequest,
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_context)
):
    """
    Handle PhonePe payment callback
    """
    try:
        # Find the transaction
        transaction = db.query(PaymentTransaction).filter(
            and_(
                PaymentTransaction.order_id == request.order_id,
                PaymentTransaction.workspace_id == workspace_id
            )
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Verify signature (simplified for demo)
        # In production, this would use PhonePe's signature verification
        is_valid = verify_phonepe_signature(request)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Update transaction status
        transaction.status = request.status.lower()
        transaction.completed_at = datetime.utcnow()
        transaction.provider_response = request.dict()
        
        # If payment successful, create/update subscription
        if request.status.lower() == "completed":
            await activate_subscription(db, workspace_id, request.plan_id, transaction.id)
        
        db.commit()
        
        logger.info(f"Payment callback processed for order {request.order_id}: {request.status}")
        return SuccessResponse(message="Payment callback processed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment callback processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions", response_model=SubscriptionResponse)
async def get_subscription(
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_context)
):
    """
    Get current subscription details
    """
    try:
        subscription = db.query(Subscription).filter(
            and_(
                Subscription.workspace_id == workspace_id,
                Subscription.status.in_(["active", "trialing"])
            )
        ).first()
        
        if not subscription:
            # Return default subscription info
            return SubscriptionResponse(
                id="",
                plan_id="free",
                plan_name="Free Plan",
                status="active",
                start_date=datetime.utcnow(),
                end_date=None,
                price_paid=0.0,
                currency="USD",
                current_usage={"assets": 0, "api_calls": 0},
                limits={"assets": 10, "api_calls": 1000},
                features=["Basic asset creation", "Community support"],
                next_billing_date=None
            )
        
        # Get plan details
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        
        return SubscriptionResponse(
            id=subscription.id,
            plan_id=plan.plan_id if plan else subscription.plan_id,
            plan_name=plan.name if plan else "Unknown Plan",
            status=subscription.status,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            price_paid=subscription.price_paid,
            currency=subscription.currency,
            current_usage=subscription.current_usage or {},
            limits=plan.limits if plan else {},
            features=plan.features if plan else [],
            next_billing_date=subscription.end_date
        )
        
    except Exception as e:
        logger.error(f"Subscription retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/subscriptions/cancel", response_model=SuccessResponse)
async def cancel_subscription(
    db: Session = Depends(get_db),
    workspace_id: str = Depends(get_workspace_context)
):
    """
    Cancel or downgrade subscription
    """
    try:
        subscription = db.query(Subscription).filter(
            and_(
                Subscription.workspace_id == workspace_id,
                Subscription.status.in_(["active", "trialing"])
            )
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Update subscription status
        subscription.status = "canceled"
        subscription.canceled_at = datetime.utcnow()
        subscription.cancel_reason = "User requested cancellation"
        
        db.commit()
        
        logger.info(f"Subscription {subscription.id} canceled for workspace {workspace_id}")
        return SuccessResponse(message="Subscription canceled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    db: Session = Depends(get_db)
):
    """
    List available subscription plans
    """
    try:
        plans = db.query(Plan).filter(
            and_(
                Plan.is_active == True,
                Plan.is_public == True
            )
        ).order_by(Plan.price).all()
        
        return [
            PlanResponse(
                id=plan.id,
                plan_id=plan.plan_id,
                name=plan.name,
                description=plan.description,
                price=plan.price,
                currency=plan.currency,
                billing_interval=plan.billing_interval,
                features=plan.features or [],
                limits=plan.limits or {},
                is_active=plan.is_active
            )
            for plan in plans
        ]
        
    except Exception as e:
        logger.error(f"Plan listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def verify_phonepe_signature(request: PaymentCallbackRequest) -> bool:
    """
    Verify PhonePe callback signature
    In production, this would use PhonePe's actual signature verification
    """
    # Simplified verification for demo
    # In reality, you would:
    # 1. Concatenate specific fields in a specific order
    # 2. Calculate HMAC SHA256 hash with your salt key
    # 3. Compare with the received signature
    
    data_string = f"{request.order_id}|{request.transaction_id}|{request.status}"
    if request.amount:
        data_string += f"|{request.amount}"
    if request.currency:
        data_string += f"|{request.currency}"
    
    calculated_signature = hmac.new(
        PHONEPE_SALT_KEY.encode(),
        data_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # For demo, we'll assume signature is valid
    # In production: return calculated_signature == request.signature
    return True


async def activate_subscription(
    db: Session,
    workspace_id: str,
    plan_id: str,
    transaction_id: str
):
    """
    Activate subscription after successful payment
    """
    try:
        # Get plan details
        plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        # Check if subscription already exists
        existing_subscription = db.query(Subscription).filter(
            and_(
                Subscription.workspace_id == workspace_id,
                Subscription.status.in_(["active", "trialing"])
            )
        ).first()
        
        if existing_subscription:
            # Update existing subscription
            existing_subscription.plan_id = plan.id
            existing_subscription.end_date = datetime.utcnow() + timedelta(days=30)
            existing_subscription.price_paid = plan.price
            existing_subscription.updated_at = datetime.utcnow()
        else:
            # Create new subscription
            subscription = Subscription(
                workspace_id=workspace_id,
                plan_id=plan.id,
                status="active",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                price_paid=plan.price,
                currency=plan.currency,
                current_usage={},
                usage_reset_date=datetime.utcnow() + timedelta(days=30)
            )
            db.add(subscription)
        
        db.commit()
        logger.info(f"Subscription activated for workspace {workspace_id} with plan {plan_id}")
        
    except Exception as e:
        logger.error(f"Subscription activation failed: {e}")
        raise

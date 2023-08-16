from flask import Blueprint, request, make_response
from pydantic import BaseModel, ValidationError

from src.config import config_instance
from src.database.models.users import User
from src.main import subscriptions_controller, user_controller, flutterwave_payments

flutterwave_route = Blueprint('flutterwave', __name__)

from datetime import datetime
from typing import Optional


class Customer(BaseModel):
    id: int
    name: str
    phone_number: Optional[str]
    email: str
    created_at: datetime


class Card(BaseModel):
    first_6digits: str
    last_4digits: str
    issuer: str
    country: str
    type: str
    expiry: str


class WebhookData(BaseModel):
    event: str
    data: dict

    def __init__(self, **data):
        super().__init__(**data)
        self.data = self.data.get("data", {})
        self.customer = self.data.get("customer", {})
        self.card = self.data.get("card", {})

    id: Optional[int] = None
    tx_ref: Optional[str] = None
    flw_ref: Optional[str] = None
    device_fingerprint: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    charged_amount: Optional[int] = None
    app_fee: Optional[float] = None
    merchant_fee: Optional[float] = None
    processor_response: Optional[str] = None
    auth_model: Optional[str] = None
    ip: Optional[str] = None
    narration: Optional[str] = None
    status: Optional[str] = None
    payment_type: Optional[str] = None
    created_at: Optional[datetime] = None
    account_id: Optional[int] = None
    customer: Customer
    card: Card


@flutterwave_route.post('/admin/webhooks/flutterwave/<string:secret_id>')
async def flutterwave_hook(secret_id: str):
    """

    :return:
    """
    flutterwave_hash = request.headers.get("verifi-hash")
    if not flutterwave_hash:
        response = make_response()
        return "failure", 401

    if config_instance().FLUTTERWAVE_HASH != flutterwave_hash:
        return "failure", 401

    try:
        payload = WebhookData(data=request.json)
    except ValidationError:
        return "failure", 401

    user: User = await user_controller.get_by_email(email=payload.customer.email)
    if not (user and user.email):
        user: User = await user_controller.get(user_id=payload.customer.id)
        if not (user and user.email):
            return "failure", 401

    payment_receipt_updated = await subscriptions_controller.set_receipt_status(reference=payload.tx_ref,
                                                                                status=payload.status)
    if payment_receipt_updated:
        # TODO - send a verification request to flutterwave to verify that this request was accepted
        pass


@flutterwave_route.get("/admin/flutterwave/payment-link/<string:subscription_id>")
async def process_payment_link(subscription_id: str):
    """
    Find the following query parameters on this request:
    status, tx_ref, and transaction_id

    :param subscription_id: Subscription ID
    :return: Response based on payment information
    """
    status = request.args.get("status")
    tx_ref = request.args.get("tx_ref")
    transaction_id = request.args.get("transaction_id")

    if not (status and tx_ref and transaction_id):
        return "Missing required query parameters", 401

    payment_receipt = await flutterwave_payments.get_payment_details(subscription_id=subscription_id, tx_ref=tx_ref)
    if not payment_receipt:
        return "Missing required query parameters", 401

    payment_receipt_updated = await subscriptions_controller.set_receipt_status(reference=tx_ref, status=status)
    if payment_receipt_updated:
        # TODO - send a verification request to flutterwave to verify that this request was accepted
        pass

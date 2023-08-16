import requests
from flask import Flask
from pydantic import BaseModel

from src.config import config_instance
from src.database.models.subscriptions import PaymentReceipts, Subscriptions
from src.database.models.users import User


class Customer(BaseModel):
    email: str
    phonenumber: str
    name: str


class Customizations(BaseModel):
    title: str
    logo: str


class Meta(BaseModel):
    consumer_id: str
    consumer_mac: str


class PaymentDetails(BaseModel):
    tx_ref: str
    amount: int
    currency: str = "ZAR"
    redirect_uri: str
    meta: Meta
    customer: Customer
    customizations: Customizations


class PaymentResponse(BaseModel):
    status: str
    message: str
    data: dict[str, str]


class Flutterwave:

    def __init__(self):
        self._redirect_base_uri: str = "https://rental-manager.site/admin/flutterwave/payment-link/"
        self._payment_endpoint_uri: str = "https://api.flutterwave.com/v3/payments"
        self._headers = {
            "Authorization": f"Bearer {config_instance().FLUTTERWAVE_FLW_SECRET_KEY}",
            "Accept": "application/json"  # Adding the Accept header for JSON responses
        }

    def init_app(self, app: Flask):
        pass

    async def _payment_link(self, subscription_id: str) -> str:
        return f"{self._redirect_base_uri}{subscription_id}"

    async def create_payment_details(self, user: User, payment_receipt: PaymentReceipts,
                                     subscription: Subscriptions) -> PaymentDetails:
        """

        :param subscription:
        :param user:
        :param payment_receipt:
        :return:
        """
        payment_details = dict(
            tx_ref=payment_receipt.reference,
            amount=payment_receipt.payment_amount,
            currency="ZAR",
            redirect_uri=self._payment_link(subscription_id=payment_receipt.subscription_id),
            meta=dict(user_id=payment_receipt.user_id, subscription_id=payment_receipt.subscription_id),
            customer=dict(email=user.email, phonenumber=user.contact_number, name=user.full_name),
            customizations=dict(title=subscription.plan.name, logo=config_instance().LOGO_URL)
        )
        return PaymentDetails(**payment_details)

    async def get_payment_link(self, payment_details: PaymentDetails) -> PaymentResponse:
        response = requests.post(url=self._payment_endpoint_uri, data=payment_details.dict(), headers=self._headers)

        if response.status_code not in [200, 201]:
            return PaymentResponse(status="error", message="Request failed", data={})
        try:
            response_data = response.json()
            payment_response = PaymentResponse(**response_data)
            return payment_response
        except (ValueError, KeyError):
            # Handle parsing errors
            return PaymentResponse(status="error", message="Failed to parse response", data={})

    async def get_payment_details(self, subscription_id: str, tx_ref: str) -> PaymentReceipts:
        """
            **get_payment_details**

        :param subscription_id:
        :param tx_ref:
        :return:
        """

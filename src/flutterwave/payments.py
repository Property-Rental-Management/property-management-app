import uuid

from pydantic import BaseModel


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

    async def _payment_link(self) -> str:
        _uuid = str(uuid.uuid4())
        return f"{self._redirect_base_uri}{_uuid}"

    async def create_payment(self, payment_details: PaymentDetails):
        pass

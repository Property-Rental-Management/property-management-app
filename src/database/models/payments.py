from datetime import date, datetime

from pydantic import BaseModel, Field

from src.database.tools import create_transaction_id


def create_date_paid() -> date:
    return datetime.now().date()


class Payment(BaseModel):
    """
    Represents a payment transaction.
   """
    transaction_id: str
    invoice_number: int
    tenant_id: str
    property_id: str
    unit_id: str
    amount_paid: int
    date_paid: date
    payment_method: str
    is_successful: bool
    month: int
    comments: str


class CreatePayment(BaseModel):
    """
    Represents a payment transaction.
   """
    transaction_id: str = Field(default_factory=create_transaction_id, description="BankTransaction ID")
    invoice_number: int
    tenant_id: str
    property_id: str
    unit_id: str
    amount_paid: int
    date_paid: date = Field(default_factory=lambda: create_date_paid())
    payment_method: str | None
    is_successful: bool = Field(default=False)
    month: int | None
    comments: str | None


class UnitInvoicePaymentForm(BaseModel):
    invoice_number: int
    tenant_id: str
    property_id: str
    unit_id: str
    amount_paid: int
    payment_verified: bool = Field(default=False)

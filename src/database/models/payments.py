from datetime import date
from pydantic import BaseModel, Field
from src.database.tools import create_transaction_id


class Payment(BaseModel):
    """
    Represents a payment transaction.

    Attributes:
        transaction_id (str): BankTransaction ID.
        tenant_id (str): ID of the tenant making the payment.
        property_id (str): ID of the property for which the payment is made.
        amount (float): Payment rental_amount.
        date (date): Date of the payment.
        payment_method (str): Payment method used.
        is_successful (bool): Indicates whether the payment was successful.
        rental_period_start (date): Start date of the rental period.
        rental_period_end (date): End date of the rental period.
        rental_unit (str): Rental unit information.
        comments (str): Additional comments or notes.
    """
    transaction_id: str = Field(default_factory=create_transaction_id, description="BankTransaction ID")
    tenant_id: str
    property_id: str
    amount: float
    date: date
    payment_method: str
    is_successful: bool
    rental_period_start: date
    rental_period_end: date
    rental_unit: str
    comments: str

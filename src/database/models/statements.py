import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from src.database.models.invoices import Invoice
from src.database.models.payments import Payment


class Statement(BaseModel):
    """
    Represents a statement.

    Attributes:
    - statement_id (str): The unique ID of the statement.
    - tenant_id (str): The ID of the tenant associated with the statement.
    - month (str): The month of the statement.
    - rental_amount (float): The rental_amount of the statement.
    - items (list[StatementItem]): A list of items included in the statement.
    - payments (list[Payment]): A list of payments made for the statement.
    - is_paid (bool): Indicates if the statement has been paid.
    - payment_date (datetime): The date of payment.
    - generated_at (datetime): The date when the statement was generated.
    """

    statement_id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                              description="The unique ID of the statement.")
    tenant_id: str
    month: int
    invoices: list[Invoice]
    payments: list[Payment]
    is_paid: bool
    payment_date: datetime
    generated_at: datetime = Field(default_factory=datetime.now,
                                   description="The date when the statement was generated.")

    @property
    def total_invoiced(self) -> int:
        return sum(invoice.amount_payable for invoice in self.invoices)

    @property
    def total_payments(self) -> int:
        return sum(payment.amount_paid for payment in self.payments)

    @property
    def balance(self) -> int:
        return self.total_invoiced - self.total_payments

    def create_tenant_monthly_statements(self, year: int, month: int) -> list[Self]:
        """

        :param year:
        :param month:
        :return:
        """
        pass

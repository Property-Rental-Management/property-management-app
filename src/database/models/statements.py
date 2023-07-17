import uuid
from datetime import datetime, date
from typing import Self

from pydantic import BaseModel, Field

from database.models.companies import Company
from src.database.models.invoices import Invoice
from src.database.models.payments import Payment


class CreateStatement(BaseModel):
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

    statement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement_number: int
    tenant_id: str
    year: int
    month: int
    statement_period: tuple[date, date]
    company: Company
    invoices: list[Invoice]
    payments: list[Payment]
    statement_date: date = Field(default_factory=lambda: datetime.now().date())

    @property
    def total_invoiced(self) -> int:
        return sum(invoice.amount_payable for invoice in self.invoices)

    @property
    def total_payments(self) -> int:
        return sum(payment.amount_paid for payment in self.payments)

    @property
    def balance(self) -> int:
        return self.total_invoiced - self.total_payments

    async def load_company(self):
        """

        :return:
        """
        pass

    async def load_invoices(self, month: int) -> None:
        from src.main import lease_agreement_controller
        invoices = []
        if self.tenant_id:
            invoices = await lease_agreement_controller.get_invoices(tenant_id=self.tenant_id)
        self.invoices = [invoice for invoice in invoices if invoice.month == month]

    async def load_payments(self, month: int):
        from src.main import lease_agreement_controller
        payments = []
        if self.tenant_id:
            payments = await lease_agreement_controller.load_tenant_payments(tenant_id=self.tenant_id)
        self.payments = [payment for payment in payments if payment.date_paid.month == month]

    def create_tenant_monthly_statement(self, year: int, month: int) -> Self:
        """
            **will create statement only for the present month
        :param year:
        :param month:
        :return:
        """
        await self.load_company()
        await self.load_invoices(month=month)
        await self.load_payments(month=month)
        # Generate a statement for the specified year and month
        return self

    def dict(self):
        return {
            'statement_id': self.statement_id,
            'tenant_id': self.tenant_id,
            'month': self.month,
            'invoices': [invoice.dict() for invoice in self.invoices],
            'payments': [payment.dict() for payment in self.payments],
            'statement_date': self.statement_date,
            'total_invoiced': self.total_invoiced,
            'total_payments': self.total_payments,
            'balance': self.balance
        }

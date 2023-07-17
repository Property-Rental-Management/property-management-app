import uuid
from datetime import date
from typing import Self

from pydantic import BaseModel, Field

from database.models.companies import Company
from database.models.properties import Property
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
    statement_number: int | None
    tenant_id: str | None
    year: int | None
    month: int | None
    statement_period: tuple[date, date]
    company: Company | None
    invoices: list[Invoice] | None
    payments: list[Payment] | None

    def init(self, statement_number: int, tenant_id: str, statement_period: tuple[date, date]) -> Self:
        self.tenant_id = tenant_id
        self.statement_number = statement_number
        self.month = statement_period[0].month
        self.year = statement_period[0].year
        self.statement_period = statement_period
        self.company = None
        self.invoices = []
        self.payments = []
        return self

    @property
    def statement_date(self) -> date | None:
        if self.statement_period:
            return max(self.statement_period)
        return None

    @property
    def total_invoiced(self) -> int:
        return sum(invoice.amount_payable for invoice in self.invoices)

    @property
    def total_payments(self) -> int:
        return sum(payment.amount_paid for payment in self.payments)

    @property
    def balance(self) -> int:
        return self.total_invoiced - self.total_payments

    async def load_company(self, property_id: str):
        """

        :return:
        """
        from src.main import company_controller
        building: Property = await company_controller.get_property_by_id_internal(property_id=property_id)
        company: Company = await company_controller.get_company_internal(company_id=building.company_id)
        self.company = company if company else None

    async def load_invoices(self, month: int, year: int) -> None:
        from src.main import lease_agreement_controller
        invoices = []
        if self.tenant_id:
            invoices = await lease_agreement_controller.get_invoices(tenant_id=self.tenant_id)
        self.invoices = [invoice for invoice in invoices
                         if (invoice.due_date.month == month and invoice.due_date.year == year)]

    async def load_payments(self, month: int, year: int):
        from src.main import lease_agreement_controller
        payments = []
        if self.tenant_id:
            payments = await lease_agreement_controller.load_tenant_payments(tenant_id=self.tenant_id)
        self.payments = [payment for payment in payments
                         if (payment.date_paid.month == month and payment.date_paid.year == year)]

    async def create_month_statement(self, year: int, month: int) -> Self:
        """
            **will create statement only for the stated month
        :param year:
        :param month:
        :return:
        """
        if not self.tenant_id:
            return self

        await self.load_invoices(month=month, year=year)
        await self.load_payments(month=month, year=year)

        if self.payments:
            payment: Payment = self.payments[0]
            property_id = payment.property_id
            await self.load_company(property_id=property_id)
            # Generate a statement for the specified year and month

        return self

    async def create_all_statements(self, start_year: int, end_year: int):
        statements = []

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                await self.create_month_statement(year, month)
                statements.append(self.dict())

        return statements

    def dict(self):
        return {
            'statement_id': self.statement_id,
            'tenant_id': self.tenant_id,
            'month': self.month,
            'statement_period': [_date for _date in self.statement_period] if self.statement_period else None,
            'company': self.company.dict() if self.company else None,
            'invoices': [invoice.dict() for invoice in self.invoices] if self.invoices else None,
            'payments': [payment.dict() for payment in self.payments] if self.payments else None,
            'statement_date': self.statement_date,
            'total_invoiced': self.total_invoiced,
            'total_payments': self.total_payments,
            'balance': self.balance
        }

from pydantic import BaseModel

from database.models.payments import Payment


class MonthlyCashFlow(BaseModel):
    """
    Represents the cash flow for a specific month.
    """
    month: int
    cashflow: int
    property_id: str
    tenant_id: str
    unit_id: str


class CashFlowModel(BaseModel):
    """
    Represents the overall cash flow model.
    """
    payments: list[Payment]

    @property
    def monthly_cashflow(self) -> dict[int, MonthlyCashFlow]:
        monthly_cashflows = {}

        for payment in self.payments:
            if payment.is_successful:
                month = payment.date_paid.month
                amount_paid = payment.amount_paid
                property_id = payment.property_id
                tenant_id = payment.tenant_id
                unit_id = payment.unit_id

                if month in monthly_cashflows:
                    monthly_cashflows[month].cashflow += amount_paid
                else:
                    monthly_cashflows[month] = MonthlyCashFlow(
                        month=month,
                        cashflow=amount_paid,
                        property_id=property_id,
                        tenant_id=tenant_id,
                        unit_id=unit_id,
                    )

        return monthly_cashflows

    @property
    def total_cashflow(self) -> int:
        return sum(monthly_cashflow.cashflow for monthly_cashflow in self.monthly_cashflow.values())

    def monthly_cashflow_by_property(self, property_id: str) -> list[MonthlyCashFlow]:
        cashflow_by_property = []

        for monthly_cash_flow in self.monthly_cashflow.values():
            if monthly_cash_flow.property_id == property_id:
                cashflow_by_property.append(monthly_cash_flow)

        return cashflow_by_property

    def monthly_cashflow_by_unit(self, unit_id: str) -> list[MonthlyCashFlow]:
        cashflow_by_unit = []

        for monthly_cash_flow in self.monthly_cashflow.values():
            if monthly_cash_flow.unit_id == unit_id:
                cashflow_by_unit.append(monthly_cash_flow)

        return cashflow_by_unit

    def monthly_cashflow_by_tenant(self, tenant_id: str) -> list[MonthlyCashFlow]:
        cashflow_by_tenant = []
        for monthly_cash_flow in self.monthly_cashflow.values():
            if monthly_cash_flow.tenant_id == tenant_id:
                cashflow_by_tenant.append(monthly_cash_flow)

        return cashflow_by_tenant

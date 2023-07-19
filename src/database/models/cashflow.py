from pydantic import BaseModel

from src.database.models.payments import Payment
from src.logger import init_logger

cashflow_logger = init_logger('cashflow_logger')

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
    company_id: str | None
    payments: list[Payment] | None

    def init(self, company_id: str):
        self.company_id = company_id

    def load_payments(self):
        """
            **load_payments**
        :return:
        """
        from src.main import lease_agreement_controller
        if not self.company_id:
            return
        _payments = lease_agreement_controller.sync_load_company_payments(company_id=self.company_id)
        self.payments = _payments

    async def monthly_cashflow(self) -> dict[int, MonthlyCashFlow]:
        monthly_cashflows = {}
        self.load_payments()
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

    async def total_cashflow(self) -> int:
        monthly_cashflows = await self.monthly_cashflow()
        return sum(monthly_cashflow.cashflow for monthly_cashflow in monthly_cashflows.values())

    async def monthly_cashflow_by_property(self) -> dict[str, MonthlyCashFlow]:
        from src.main import company_controller
        cashflow_by_property = {}

        buildings = await company_controller.get_properties_internal(company_id=self.company_id)
        property_ids = [building.property_id for building in buildings]
        cashflow_logger.info(f"Property IDS : {property_ids}")
        self.load_payments()
        for payment in self.payments:
            if payment.property_id in property_ids:
                if payment.is_successful:
                    month = payment.date_paid.month
                    amount_paid = payment.amount_paid
                    property_id = payment.property_id
                    tenant_id = payment.tenant_id
                    unit_id = payment.unit_id

                    if payment.property_id in cashflow_by_property:
                        cashflow_by_property[payment.property_id].cashflow += amount_paid
                    else:
                        cashflow_by_property[payment.property_id] = MonthlyCashFlow(
                            month=month,
                            cashflow=amount_paid,
                            property_id=property_id,
                            tenant_id=tenant_id,
                            unit_id=unit_id,
                        )

        return cashflow_by_property

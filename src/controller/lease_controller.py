from database.models.invoices import Invoice
from src.database.models.invoices import Invoice, UnitCharge
from src.database.sql.invoices import InvoiceORM, ItemsORM, UserChargesORM
from src.logger import init_logger
from src.database.sql import Session
from src.controller import error_handler
from src.database.sql.lease import LeaseAgreementORM
from src.database.models.lease import LeaseAgreement, CreateLeaseAgreement


class LeaseController:
    def __init__(self):
        self._logger = init_logger(self.__class__.__name__)

    @error_handler
    async def get_all_active_lease_agreements(self) -> list[LeaseAgreement]:
        with Session() as session:
            lease_agreements: list[LeaseAgreementORM] = session.query(LeaseAgreementORM).filter(
                LeaseAgreementORM.is_active == True).all()
            return [LeaseAgreement(**lease.dict()) for lease in lease_agreements]

    @error_handler
    async def create_lease_agreement(self, lease: CreateLeaseAgreement) -> LeaseAgreement | None:
        """
            **create_lease_agreement**
                create lease agreement
        :param lease:
        :return:
        """
        with Session() as session:
            try:
                lease_orm: LeaseAgreementORM = LeaseAgreementORM(**lease.dict())
                session.add(lease_orm)
                session.commit()
                return LeaseAgreement(**lease.dict())
            except Exception as e:
                self._logger.error(f"Error creating Lease Agreement:  {str(e)}")
            return None

    @staticmethod
    async def calculate_deposit_amount(rental_amount: int) -> int:
        """
            **calculate_deposit_amount**
                calculate deposit rental_amount

        :param rental_amount:
        :return:
        """
        # TODO - calculate deposit rental_amount based on user profile settings
        return rental_amount * 2

    @staticmethod
    async def get_agreements_by_payment_terms(self, payment_terms: str = "monthly") -> list[LeaseAgreement]:
        with Session() as session:
            try:
                lease_orm_list: list[LeaseAgreementORM] = session.query(LeaseAgreementORM).filter(
                    LeaseAgreementORM.is_active == True, LeaseAgreementORM.payment_period == payment_terms).all()
                return [LeaseAgreement(**lease.dict()) for lease in lease_orm_list if lease] if lease_orm_list else []
            except Exception as e:
                self._logger.error(f"Error creating Lease Agreement:  {str(e)}")
            return []

    @error_handler
    async def get_invoice(self, invoice_number: str) -> Invoice:
        """

        :param invoice_number:

        :return:
        """
        with Session() as session:
            invoice_orm: InvoiceORM = session.query(InvoiceORM).filter(
                InvoiceORM.invoice_number == invoice_number).first()
            return Invoice(**invoice_orm.to_dict())

    @error_handler
    async def create_invoice(self, invoice_charges: list[UnitCharge], unit_: Unit):
        """

        :param invoice_charges:
        :param unit_:
        :return:
        """
        #todo obtain property - using unit_.property_id
        #todo obtain company details using property
        # todo obtain tenant usint unit_.tenant_id
        service_name: str = f"{property_.name} Invoice"
        description: str = f"{company.company_name} Monthly Rental Invoice for Property : {property_.name}"
        _date_issued = datetime.now().date()
        _due_date = await self.calculate_due_date(date_issued=_date_issued)
        _invoice_data = dict(service_name=service_name, description=description, currency=profile.currency,
                             customer=dict(tenant_id=tenant.tenant_id, name=tenant.name, email=tenant.email,
                                           cell=tenant.cell),
                             date_issued=_date_issued, due_date=_due_date, invoiced_items=_invoiced_items)

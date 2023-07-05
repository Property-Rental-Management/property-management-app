import uuid
from datetime import datetime, date
from src.database.models.companies import Company
from src.database.models.invoices import Invoice
from src.database.models.tenants import Tenant
from src.database.sql.tenants import TenantORM
from src.database.sql.companies import CompanyORM
from src.database.models.properties import Unit, Property
from src.database.sql.properties import PropertyORM
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
    async def create_invoice(self, invoice_charges: list[UnitCharge], unit_: Unit) -> Invoice:
        """

        :param invoice_charges:
        :param unit_:
        :return:
        """
        # todo obtain property - using unit_.property_id
        # todo obtain company details using property
        # todo obtain tenant usint unit_.tenant_id
        with Session() as session:
            try:
                _property_id = unit_.property_id if unit_ else None
                if unit_ and unit_.property_id:
                    _property_id = unit_.property_id

                if (_property_id is None) and invoice_charges:
                    property_id = invoice_charges[0].property_id
                else:
                    property_id = _property_id

                property_orm = session.query(PropertyORM).filter(PropertyORM.property_id == property_id).first()
                company_orm = session.query(CompanyORM).filter(CompanyORM).first()
                tenant_id = invoice_charges[0].tenant_id if invoice_charges else unit_.tenant_id
                tenant_orm = session.query(TenantORM).filter(TenantORM.tenant_id == tenant_id).first()
                property_: Property = Property(**property_orm.to_dict())
                company: Company = Company(**company_orm.to_dict())
                tenant: Tenant = Tenant(**tenant_orm.to_dict())

                service_name: str = f"{property_.name} Invoice"
                description: str = f"{company.company_name} Monthly Rental Invoice for Property : {property_.name}"
                date_issued: date = datetime.now().date()
                due_date: date = await self.calculate_due_date(date_issued=date_issued)
                list_charge_ids = await self.get_charge_ids(invoice_charges=invoice_charges)
                charge_ids: str = ",".join(list_charge_ids)

                invoice_orm: InvoiceORM = InvoiceORM(invoice_number=str(uuid.uuid4()), service_name=service_name,
                                                     description=description, currency="R", tenant_id=tenant.tenant_id,
                                                     discount=0, tax_rate=0, date_issued=date_issued, due_date=due_date,
                                                     month=due_date.month, rental_amount=unit_.rental_amount,
                                                     charge_ids=charge_ids, invoice_sent=False, invoice_printed=False)

                session.add(invoice_orm)
                session.commit()
            except Exception as e:
                print(str(e))
        return Invoice(**invoice_orm.to_dict())

    @staticmethod
    async def calculate_due_date(date_issued: date) -> date:
        if date_issued.day >= 7:
            if date_issued.month == 12:
                due_date = date(date_issued.year + 1, 1, 7)
            else:
                due_date = date(date_issued.year, date_issued.month + 1, 7)
        else:
            due_date = date(date_issued.year, date_issued.month, 7)

        return due_date

    @staticmethod
    async def get_charge_ids(invoice_charges: list[UnitCharge]) -> list[str]:
        """

        :param invoice_charges:
        :return:
        """
        return [charge.charge_id for charge in invoice_charges if charge] if invoice_charges else []

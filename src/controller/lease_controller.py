from datetime import datetime, date

from pydantic import ValidationError

from src.controller import error_handler, Controllers
from src.database.models.companies import Company
from src.database.models.invoices import Invoice, UnitCharge
from src.database.models.lease import LeaseAgreement, CreateLeaseAgreement
from src.database.models.properties import Unit, Property
from src.database.models.tenants import Tenant
from src.database.sql import Session
from src.database.sql.companies import CompanyORM
from src.database.sql.invoices import InvoiceORM, UserChargesORM
from src.database.sql.lease import LeaseAgreementORM
from src.database.sql.properties import PropertyORM
from src.database.sql.tenants import TenantORM
from src.logger import init_logger


class LeaseController(Controllers):
    def __init__(self):
        super().__init__()
        self._logger = init_logger(self.__class__.__name__)

    @error_handler
    async def get_all_active_lease_agreements(self) -> list[LeaseAgreement]:
        with self.get_session() as session:
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
        with self.get_session() as session:
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
        return rental_amount * 2

    async def get_agreements_by_payment_terms(self, payment_terms: str = "monthly") -> list[LeaseAgreement]:
        """
        **get_agreements_by_payment_terms**

        :param self:
        :param payment_terms:
        :return:
        """
        with self.get_session() as session:
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
            **get_invoice**
        :param invoice_number:

        :return:
        """
        with self.get_session() as session:
            invoice_orm: InvoiceORM = session.query(InvoiceORM).filter(
                InvoiceORM.invoice_number == invoice_number).first()
            return Invoice(**invoice_orm.to_dict())

    async def create_invoice(self, invoice_charges: list[UnitCharge], unit_: Unit,
                             include_rental: bool = False) -> Invoice | None:
        """
            **create_invoice**
                will attempt to create an invoice if success returns an invoice on failure returns None
        :param include_rental:
        :param invoice_charges:
        :param unit_:
        :return:
        """
        with self.get_session() as session:
            try:
                _property_id: str = unit_.property_id if unit_ and unit_.property_id else None
                property_id: str = _property_id if _property_id is not None else invoice_charges[0].property_id \
                    if invoice_charges else None

                property_orm: PropertyORM = session.query(PropertyORM).filter(
                    PropertyORM.property_id == property_id).first()
                company_orm: CompanyORM = session.query(CompanyORM).first()

                tenant_id: str = invoice_charges[0].tenant_id if invoice_charges else unit_.tenant_id
                tenant_orm: TenantORM = session.query(TenantORM).filter(TenantORM.tenant_id == tenant_id).first()

                property_: Property = Property(**property_orm.to_dict()) if property_orm else None
                company: Company = Company(**company_orm.to_dict()) if company_orm else None
                tenant: Tenant = Tenant(**tenant_orm.to_dict()) if tenant_orm else None

                if (property_ is None) or (company is None) or (tenant is None):
                    self._logger.error(f"""                    
                    Error -- !                                        
                    Property : {property_}                    
                    Company : {company}                    
                    Tenant : {tenant}
                    """)
                    return None
                else:
                    self._logger.debug(f"""                    
                    Error -- !                                        
                    Property : {property_}                    
                    Company : {company}                    
                    Tenant : {tenant}
                    """)

                service_name: str = f"{property_.name} Invoice" if property_.name else None
                description: str = f"{company.company_name} Monthly Rental for a Unit on {property_.name}" \
                    if company.company_name and property_.name else None

                if service_name is None or description is None:
                    self._logger.error(f"""
                    This should not happen : 
                    Service Name: {service_name} & Description: {description}""")
                    return None

                date_issued: date = datetime.now().date()
                due_date: date = await self.calculate_due_date(date_issued=date_issued)

                list_charge_ids: list[str] = await self.get_charge_ids(invoice_charges=invoice_charges) \
                    if invoice_charges else []

                charge_ids = ",".join(list_charge_ids) if list_charge_ids else []
                # TODO - should use Pydantic here to enable an extra layer of data verification before creating ORM
                # this will set rent to zero if it should not be included on invoice
                _rental_amount = unit_.rental_amount if include_rental else 0
                try:
                    invoice_orm: InvoiceORM = InvoiceORM(service_name=service_name, description=description,
                                                         currency="R", tenant_id=tenant.tenant_id, discount=0,
                                                         tax_rate=0, date_issued=date_issued, due_date=due_date,
                                                         month=due_date.month, rental_amount=_rental_amount,
                                                         charge_ids=charge_ids, invoice_sent=False,
                                                         invoice_printed=False)

                    self._logger.info(f"Invoice ORM : {invoice_orm}")

                except Exception as e:
                    self._logger.error(str(e))
                # TODO - find a way to allow user to indicate Discount and Tax Rate - preferrably Tax rate can be set on
                #  settings
                session.add(invoice_orm)
                session.commit()

                try:
                    _response: Invoice = Invoice(**invoice_orm.to_dict())
                except ValidationError as e:
                    self._logger.error(str(e))
                self._logger.info(f"Invoice Created Successfully : {_response}")

                # NOTE: marking user charges as invoiced
                await self.mark_charges_as_invoiced(session=session, charge_ids=list_charge_ids)
                return _response

            except Exception as e:
                self._logger.error(str(e))

            return None

    @staticmethod
    async def calculate_due_date(date_issued: date) -> date:
        """
            **calculate_due_date**
        :param date_issued:
        :return:
        """
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
            **get_charge_ids**

        :param invoice_charges:
        :return: list[str]
        """
        return [charge.charge_id for charge in invoice_charges if charge] if invoice_charges else []

    @staticmethod
    async def mark_charges_as_invoiced(session: Session, charge_ids: list[str]):
        """

        :param session:
        :param charge_ids:
        :return:
        """
        for _id in charge_ids:
            user_charge: UserChargesORM = session.query(UserChargesORM).filter(UserChargesORM.charge_id == _id).first()
            user_charge.is_invoiced = True
            session.merge(user_charge)
            session.commit()

    async def get_invoices(self, tenant_id: str) -> list[Invoice]:
        """
            **get_invoices**
        :return:
        """
        with self.get_session() as session:
            invoice_list: list[InvoiceORM] = session.query(InvoiceORM).filter(InvoiceORM.tenant_id == tenant_id).all()
            return [Invoice(**_invoice.to_dict()) for _invoice in invoice_list if _invoice] if invoice_list else []

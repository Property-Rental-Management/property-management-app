import os
import pickle
from datetime import datetime, date, timedelta

from flask import Flask, url_for
from pydantic import ValidationError

from src.controller import error_handler, Controllers
from src.database.models.companies import Company
from src.database.models.invoices import Invoice, UnitCharge
from src.database.models.lease import LeaseAgreement, CreateLeaseAgreement
from src.database.models.payments import Payment, UpdatePayment
from src.database.models.properties import Unit, Property
from src.database.models.tenants import Tenant
from src.database.sql import Session
from src.database.sql.companies import CompanyORM
from src.database.sql.invoices import InvoiceORM, UserChargesORM
from src.database.sql.lease import LeaseAgreementORM
from src.database.sql.payments import PaymentORM
from src.database.sql.properties import PropertyORM, UnitORM
from src.database.sql.tenants import TenantORM
from src.logger import init_logger


class LeaseController(Controllers):
    def __init__(self):
        super().__init__()
        self.lease_agreements: list[LeaseAgreement] = []
        # NOTE: invoices could be buggy
        self.invoices: list[Invoice] = []
        self.payments: list[Payment] = []

    def manage_invoice_list(self, invoice_instance: Invoice):

        for index, invoice in enumerate(self.invoices):
            if invoice == invoice_instance:
                # Tenant already exists, remove the existing instance
                self.invoices.pop(index)
                self.invoices.append(invoice_instance)
                break
        else:
            # Tenant instance not found, add the new instance to the list
            self.invoices.append(invoice_instance)

    def manage_payment_list(self, payment_instance: Payment):
        """

        :param payment_instance:
        :return:
        """
        for index, payment in enumerate(self.payments):
            if payment == payment_instance:
                # Tenant already exists, remove the existing instance
                self.payments.pop(index)
                self.payments.append(payment_instance)
                break
        else:
            # Tenant instance not found, add the new instance to the list
            self.payments.append(payment_instance)

    def manage_lease_list(self, lease_instance: LeaseAgreement):

        for index, lease in enumerate(self.lease_agreements):
            if lease == lease_instance:
                # Tenant already exists, remove the existing instance
                self.lease_agreements.pop(index)
                self.lease_agreements.append(lease_instance)
                break
        else:
            # Tenant instance not found, add the new instance to the list
            self.lease_agreements.append(lease_instance)

    def load_data(self):
        with self.get_session() as session:
            try:
                self.lease_agreements = [LeaseAgreement(**lease.to_dict())
                                         for lease in session.query(LeaseAgreementORM).filter().all()]
            except ValidationError as e:
                self.logger.error(f"Error loading lease agreements on start_up: {str(e)}")

            try:
                self.invoices = [Invoice(**invoice_orm.to_dict()) for invoice_orm in
                                 session.query(InvoiceORM).filter().all()]
            except ValidationError as e:
                self.logger.error(f"Error loading invoices on start_up: {str(e)}")
            try:
                self.payments = [Payment(**payment_orm.to_dict()) for payment_orm in
                                 session.query(PaymentORM).filter().all()]
            except ValidationError as e:
                self.logger.error(f"Error loading payments on start_up event: {str(e)}")

    def init_app(self, app: Flask):
        self.load_data()

    @error_handler
    async def get_all_active_lease_agreements(self) -> list[LeaseAgreement]:
        if self.lease_agreements:
            return [lease for lease in self.lease_agreements if lease.is_active]

        with self.get_session() as session:
            lease_agreements = session.query(LeaseAgreementORM).filter(LeaseAgreementORM.is_active == True).all()
            return [LeaseAgreement(**lease.dict())
                    for lease in lease_agreements] if lease_agreements else []

    @error_handler
    async def create_lease_agreement(self, lease: CreateLeaseAgreement) -> LeaseAgreement | None:
        """
            **create_lease_agreement**
                create lease agreement
        :param lease:
        :return:
        """
        with self.get_session() as session:
            lease_orm: LeaseAgreementORM = LeaseAgreementORM(**lease.dict())
            session.add(lease_orm)
            session.commit()

            lease_data = LeaseAgreement(**lease.dict())
            self.lease_agreements.append(lease_data)
            return lease_data

    @staticmethod
    async def calculate_deposit_amount(rental_amount: int) -> int:
        """
            **calculate_deposit_amount**
                calculate deposit rental_amount

        :param rental_amount:
        :return:
        """
        return rental_amount * 2

    @error_handler
    async def get_agreements_by_payment_terms(self, payment_terms: str = "monthly") -> list[LeaseAgreement]:
        """
        **get_agreements_by_payment_terms**

        :param self:
        :param payment_terms:
        :return:
        """
        if self.lease_agreements:
            return [lease for lease in self.lease_agreements
                    if lease.is_active and lease.payment_period == payment_terms]

        with self.get_session() as session:
            try:
                lease_orm_list: list[LeaseAgreementORM] = session.query(LeaseAgreementORM).filter(
                    LeaseAgreementORM.is_active == True, LeaseAgreementORM.payment_period == payment_terms).all()

                return [LeaseAgreement(**lease.dict()) for lease in lease_orm_list if lease] if lease_orm_list else []

            except Exception as e:
                self.logger.error(f"Error creating Lease Agreement:  {str(e)}")
            return []

    @error_handler
    async def get_invoice(self, invoice_number: str) -> Invoice | None:
        """
            **get_invoice**
        :param invoice_number:

        :return:
        """
        for invoice in self.invoices:
            if invoice.invoice_number == invoice_number:
                return invoice

        with self.get_session() as session:
            invoice_orm = session.query(InvoiceORM).filter(InvoiceORM.invoice_number == invoice_number).first()
            return Invoice(**invoice_orm.to_dict()) if isinstance(invoice_orm, InvoiceORM) else None

    @error_handler
    async def update_invoice(self, invoice: Invoice):
        """
        **update_invoice**
        :param invoice:
        :return:
        """
        with self.get_session() as session:
            invoice_orm: InvoiceORM = session.query(InvoiceORM).filter(
                InvoiceORM.invoice_number == invoice.invoice_number).first()

            if invoice_orm:
                # Update the attributes of the InvoiceORM instance
                invoice_orm.service_name = invoice.service_name
                invoice_orm.description = invoice.description
                invoice_orm.currency = invoice.currency
                invoice_orm.tax_rate = invoice.tax_rate

                # Commit the changes to the database
                session.commit()

                # Return the updated invoice
                invoice_data = Invoice(**invoice_orm.to_dict())
                self.manage_invoice_list(invoice_instance=invoice_data)
                return invoice_data

            return None

    @error_handler
    async def create_invoice(self, invoice_charges: list[UnitCharge], unit_: Unit,
                             include_rental: bool = False, due_after: int | None = None) -> Invoice | None:
        """
            **create_invoice**
                will attempt to create an invoice if success returns an invoice on failure returns None
        :param due_after:
        :param include_rental:
        :param invoice_charges:
        :param unit_:
        :return:
        """
        with self.get_session() as session:
            try:
                property_id: str = unit_.property_id

                property_orm: PropertyORM = session.query(PropertyORM).filter(
                    PropertyORM.property_id == property_id).first()
                company_orm: CompanyORM = session.query(CompanyORM).first()

                tenant_id: str = unit_.tenant_id
                tenant_orm: TenantORM = session.query(TenantORM).filter(TenantORM.tenant_id == tenant_id).first()

                property_: Property = Property(**property_orm.to_dict()) if property_orm else None
                company: Company = Company(**company_orm.to_dict()) if company_orm else None
                tenant: Tenant = Tenant(**tenant_orm.to_dict()) if tenant_orm else None

                if not (property_ and company and tenant):
                    self.logger.error(f"""                    
                    Error -- !                                        
                    Property : {property_}                    
                    Company : {company}                    
                    Tenant : {tenant}
                    """)
                    return None
                else:
                    self.logger.debug(f"""                    
                    Error -- !                                        
                    Property : {property_}                    
                    Company : {company}                    
                    Tenant : {tenant}
                    """)

                service_name: str = f"{property_.name} Invoice" if property_.name else None
                description: str = f"{company.company_name} Monthly Rental for a Unit on {property_.name}" \
                    if company.company_name and property_.name else None

                if not (service_name and description):
                    self.logger.error(f"""
                    This should not happen : 
                    Service Name: {service_name} & Description: {description}""")
                    return None

                date_issued: date = datetime.now().date()
                due_date: date = await self.calculate_due_date(date_issued=date_issued, due_after=due_after)

                list_charge_ids: list[str] = await self.get_charge_ids(
                    invoice_charges=invoice_charges) if invoice_charges else []

                charge_ids = ",".join(list_charge_ids) if list_charge_ids else None
                # TODO - should use Pydantic here to enable an extra layer of data verification before creating ORM
                # this will set rent to zero if it should not be included on invoice
                _rental_amount = unit_.rental_amount if include_rental else 0
                try:
                    invoice_orm: InvoiceORM = InvoiceORM(service_name=service_name, description=description,
                                                         currency="R", tenant_id=tenant.tenant_id, discount=0,
                                                         tax_rate=15, date_issued=date_issued, due_date=due_date,
                                                         month=due_date.month, rental_amount=_rental_amount,
                                                         charge_ids=charge_ids, invoice_sent=False,
                                                         invoice_printed=False)

                    self.logger.info(f"Invoice ORM : {invoice_orm}")

                except Exception as e:
                    self.logger.error(str(e))
                # TODO - find a way to allow user to indicate Discount and Tax Rate - preferrably Tax rate can be set on
                #  settings
                if not invoice_orm:
                    self.logger.error("Whoa -- BIG Trouble not creating Invoice look at the InvoiceORM")
                    return None

                session.add(invoice_orm)
                session.commit()

                try:
                    _invoice_data: Invoice = Invoice(**invoice_orm.to_dict())
                    # TODO - this could be buggy please revise
                    self.invoices.append(_invoice_data)
                except ValidationError as e:
                    self.logger.error(str(e))
                self.logger.info(f"Invoice Created Successfully : {_invoice_data}")

                # NOTE: marking user charges as invoiced
                await self.mark_charges_as_invoiced(session=session, charge_ids=list_charge_ids)

                return _invoice_data

            except Exception as e:
                self.logger.error(str(e))

            return None

    # noinspection DuplicatedCode
    @staticmethod
    @error_handler
    async def calculate_due_date(date_issued: date, due_after: int | None) -> date:
        """
            **calculate_due_date**
        :param due_after:
        :param date_issued:
        :return:
        """
        if due_after is not None:
            return date_issued + timedelta(days=due_after)

        if date_issued.day >= 7:
            if date_issued.month == 12:
                due_date = date(date_issued.year + 1, 1, 7)
            else:
                due_date = date(date_issued.year, date_issued.month + 1, 7)
        else:
            due_date = date(date_issued.year, date_issued.month, 7)

        return due_date

    @staticmethod
    @error_handler
    async def get_charge_ids(invoice_charges: list[UnitCharge]) -> list[str]:
        """
            **get_charge_ids**

        :param invoice_charges:
        :return: list[str]
        """
        return [charge.charge_id for charge in invoice_charges if charge] if invoice_charges else []

    @staticmethod
    @error_handler
    async def mark_charges_as_invoiced(session: Session, charge_ids: list[str]):
        """

        :param session:
        :param charge_ids:
        :return:
        """
        for _id in charge_ids:
            user_charge: UserChargesORM = session.query(UserChargesORM).filter(UserChargesORM.charge_id == _id).first()
            if user_charge:
                user_charge.is_invoiced = True
                session.merge(user_charge)
                session.commit()
        return None

    @error_handler
    async def get_invoices(self, tenant_id: str) -> list[Invoice]:
        """
            **get_invoices**
        :return:
        """
        if self.invoices:
            return [invoice for invoice in self.invoices if invoice.customer.tenant_id == tenant_id]

        with self.get_session() as session:
            invoice_list: list[InvoiceORM] = session.query(InvoiceORM).filter(InvoiceORM.tenant_id == tenant_id).all()
            return [Invoice(**_invoice.to_dict()) for _invoice in invoice_list if _invoice] if invoice_list else []

    @error_handler
    async def add_payment(self, payment: Payment):
        """

        :param payment:
        :return:
        """
        with self.get_session() as session:
            payment_instance = PaymentORM(**payment.dict())
            session.add(payment_instance)
            payment_data = Payment(**payment_instance.to_dict())
            session.commit()
            return payment_data

    @error_handler
    async def get_leased_unit_by_tenant_id(self, tenant_id: str) -> Unit | None:
        """

        :param tenant_id:
        :return:
        """
        with self.get_session() as session:
            unit_orm: UnitORM = session.query(UnitORM).filter(UnitORM.tenant_id == tenant_id).first()
            return Unit(**unit_orm.to_dict()) if isinstance(unit_orm, UnitORM) else None

    def load_company_payments(self, company_id: str):
        with self.get_session() as session:
            payments = []
            property_list: list[PropertyORM] = session.query(PropertyORM).filter(
                PropertyORM.company_id == company_id).all()
            for property_obj in property_list:
                payments_list = session.query(PaymentORM).filter(
                    PaymentORM.property_id == property_obj.property_id).all()
                for payment_obj in payments_list:
                    payments.append(Payment(**payment_obj.to_dict()))

        return payments

    @error_handler
    async def load_company_payments(self, company_id: str) -> list[Payment]:
        """
            **load_company_payments**
                will load a list of payments for a single company
        :param company_id:
        :return:
        """
        return self.load_company_payments(company_id=company_id)

    def sync_load_company_payments(self, company_id) -> list[Payment]:
        """

        :param company_id:
        :return:
        """
        return self.load_company_payments(company_id=company_id)

    @error_handler
    async def load_tenant_payments(self, tenant_id: str) -> list[Payment]:
        """
        **load_tenant_payments**
        Loads all payments made by the tenant.

        :param tenant_id: The ID of the tenant.
        :return: A list of payments made by the tenant.
        """
        with self.get_session() as session:
            payment_list = session.query(PaymentORM).filter(PaymentORM.tenant_id == tenant_id).all()
            return [Payment(**payment_obj.to_dict()) for payment_obj in payment_list
                    if payment_obj] if payment_list else []

    @error_handler
    async def load_payment(self, transaction_id: str) -> Payment | None:
        """
        :param transaction_id:
        :return:
        """
        with self.get_session() as session:
            transaction = session.query(PaymentORM).filter(PaymentORM.transaction_id == transaction_id).first()
            return Payment(**transaction.to_dict()) if transaction else None

    @error_handler
    async def update_payment(self, payment_instance: UpdatePayment):
        """

        :param payment_instance:
        :return:
        """
        with self.get_session() as session:
            transaction_id: str = payment_instance.transaction_id
            transaction: PaymentORM = session.query(PaymentORM).filter(
                PaymentORM.transaction_id == transaction_id).first()

            transaction.amount_paid = payment_instance.amount_paid
            transaction.date_paid = payment_instance.date_paid
            transaction.payment_method = payment_instance.payment_method
            transaction.is_successful = payment_instance.is_successful
            transaction.comments = payment_instance.comments
            session.merge(transaction)
            return Payment(**transaction.to_dict())

    @error_handler
    async def load_tenant_statements(self, tenant_id: str):
        """

        :param tenant_id:
        :return:
        """
        with self.get_session() as session:
            pass


class InvoiceManager:
    def __init__(self, cache_path):
        self.logger = init_logger(self.__class__.__name__)
        self._base_url = ""
        self._cache_path = cache_path
        self.invoices = self._load_cache()

    def init_app(self, app: Flask):
        self._base_url = app.config['BASE_URL']

    async def create_invoice_link(self, building_id: str, invoice_number: str) -> str:
        """

        :param building_id:
        :param invoice_number:
        :return:
        """
        expiration_date: datetime = datetime.now() + timedelta(days=1)
        self.logger.info(f"Invoice added will expire @: {expiration_date}")
        self.invoices[invoice_number] = expiration_date
        self._save_cache()
        url = url_for('invoices.get_invoice', invoice_number=invoice_number, building_id=building_id, _external=True)
        return url

    async def verify_invoice_number(self, invoice_number: str) -> str | None:
        expiration_date = self.invoices.get(invoice_number)
        self.logger.info(f"stored data: {self.invoices}")
        self.logger.info(f"fetching invoice number: {invoice_number} and found date: {expiration_date}")
        if expiration_date:
            if datetime.now() <= expiration_date:
                self.logger.info(f"Retrieving invoice: {invoice_number}")
                return invoice_number
            else:
                self.invoices.pop(invoice_number)
                self._save_cache()
                self.logger.info(f"The invoice {invoice_number} has expired")
        else:
            self.logger.info(f"The invoice {invoice_number} does not exist")
        return None

    def _load_cache(self):
        if os.path.isfile(self._cache_path):
            with open(self._cache_path, 'rb') as file:
                return pickle.load(file)
        return {}

    def _save_cache(self):
        with open(self._cache_path, 'wb') as file:
            pickle.dump(self.invoices, file)

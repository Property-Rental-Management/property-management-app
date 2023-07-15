from datetime import date

from pydantic import ValidationError
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, inspect

from src.database.constants import ID_LEN, NAME_LEN
from src.database.models.invoices import InvoicedItems, Customer
from src.database.sql import Base, engine, Session
from src.database.sql.tenants import TenantORM


class InvoiceORM(Base):
    """
        **InvoiceORM**

    """
    __tablename__ = 'invoices'
    invoice_number = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id: str = Column(String(ID_LEN), ForeignKey('tenants.tenant_id'))
    service_name: str = Column(String(NAME_LEN))
    description: str = Column(String(255))
    currency: str = Column(String(12))
    discount: int = Column(Integer)
    tax_rate: int = Column(Integer)
    date_issued: date = Column(Date)
    due_date: date = Column(Date)

    month: int = Column(Integer)
    rental_amount: int = Column(Integer)
    charge_ids: str = Column(Text)
    invoice_sent: bool = Column(Boolean, default=False)
    invoice_printed: bool = Column(Boolean, default=False)

    def __init__(
            self,
            tenant_id,
            service_name,
            description,
            currency,
            discount,
            date_issued,
            due_date,
            month,
            rental_amount,
            charge_ids,
            invoice_sent=False,
            invoice_printed=False,
            tax_rate=15
    ):
        self.tenant_id = tenant_id
        self.service_name = service_name
        self.description = description
        self.currency = currency
        self.discount = discount
        self.tax_rate = tax_rate
        self.date_issued = date_issued
        self.due_date = due_date
        self.month = month
        self.rental_amount = rental_amount
        self.charge_ids = charge_ids
        self.invoice_sent = invoice_sent
        self.invoice_printed = invoice_printed

    def __bool__(self) -> bool:
        """

        :return:
        """
        return bool(self.tenant_id)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self) -> dict[str, str | date | int | list[str] | dict | list[dict]]:
        """
        Convert the instance attributes to a dictionary.

        :return: A dictionary representation of the object.
        """
        return {
            "invoice_number": self.invoice_number,
            "tenant_id": self.tenant_id,
            "service_name": self.service_name,
            "description": self.description,
            "currency": self.currency,
            "discount": self.discount,
            "tax_rate": self.tax_rate,
            "date_issued": self.date_issued,
            "due_date": self.due_date,
            "month": self.month,
            "rental_amount": self.rental_amount,
            "charge_ids": self.charge_ids,
            "invoice_items": self.invoiced_items,
            "customer": self.customer,
            "invoice_sent": self.invoice_sent,
            "invoice_printed": self.invoice_printed
        }

    @property
    def invoiced_items(self) -> list[dict]:
        """
            **invoiced_items**
        :return:
        """
        _invoiced_items = []
        charge_ids = self.charge_ids
        if not charge_ids:
            return _invoiced_items
        if isinstance(charge_ids, list):
            charge_ids = ",".join(charge_ids)

        with Session() as session:
            for _charge_id in charge_ids.split(","):
                if _charge_id:
                    charge_item_orm: UserChargesORM = session.query(UserChargesORM).filter(
                        UserChargesORM.charge_id == _charge_id).first()
                    if charge_item_orm:
                        item_orm: ItemsORM = session.query(ItemsORM).filter(
                            ItemsORM.item_number == charge_item_orm.item_number).first()
                        if item_orm:
                            invoice_item_dict = dict(property_id=charge_item_orm.property_id,
                                                     item_number=charge_item_orm.item_number,
                                                     description=item_orm.description,
                                                     multiplier=item_orm.multiplier,
                                                     amount=charge_item_orm.amount)
                            try:
                                _invoiced_items.append(InvoicedItems(**invoice_item_dict).dict())
                            except ValidationError as e:
                                pass

            return _invoiced_items

    @property
    def customer(self) -> dict:
        """

        :return:
        """
        with Session() as session:
            _tenant: TenantORM = session.query(TenantORM).filter(TenantORM.tenant_id == self.tenant_id).first()
            return Customer(**_tenant.to_dict()).dict()


class ItemsORM(Base):
    """
        **ItemsORM**
        this are static Items which can appear on Tenant Charges
    """
    __tablename__ = "billable_items"
    property_id: str = Column(String(ID_LEN))
    item_number: str = Column(String(ID_LEN), primary_key=True)
    description: str = Column(String(255))
    multiplier: int = Column(Integer, default=1)
    deleted: int = Column(Boolean, default=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self) -> dict[str, str | int]:
        """
        Converts the object to a dictionary representation.

        :return: A dictionary containing the object's attributes
        """
        return {
            "property_id": self.property_id,
            "item_number": self.item_number,
            "description": self.description,
            "multiplier": self.multiplier,
            "deleted": self.deleted
        }


class UserChargesORM(Base):
    """
        **UserChargesORM**
        this allows the building admin to enter Charges for
        the building Tenant
    """
    __tablename__ = "user_invoice_charge"
    charge_id: str = Column(String(ID_LEN), primary_key=True)
    property_id: str = Column(String(ID_LEN))
    tenant_id: str = Column(String(ID_LEN))
    unit_id: str = Column(String(ID_LEN))
    item_number: str = Column(String(ID_LEN))
    month: int = Column(Integer)
    amount: int = Column(Integer)
    date_of_entry: date = Column(Date)
    is_invoiced: bool = Column(Boolean, default=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self) -> dict[str, str | date | int | bool]:
        """
        **to_dict**
        Converts the instance attributes to a dictionary.

        :return: A dictionary representation of the instance.
        """
        return {
            "charge_id": self.charge_id,
            "property_id": self.property_id,
            "tenant_id": self.tenant_id,
            "unit_id": self.unit_id,
            "item_number": self.item_number,
            "month": self.month,
            "amount": self.amount,
            "date_of_entry": self.date_of_entry,
            "is_invoiced": self.is_invoiced
        }

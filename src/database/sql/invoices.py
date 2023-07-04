from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, inspect
from datetime import date

from sqlalchemy.orm import relationship

from src.database.sql.tenants import TenantORM
from src.database.models.invoices import InvoicedItems, Customer
from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine, Session


class InvoiceORM(Base):
    __tablename__ = 'invoices'
    invoice_number: str = Column(String(ID_LEN), primary_key=True)
    tenant_id: str = Column(String(ID_LEN), ForeignKey('tenants.tenant_id'))
    service_name: str = Column(String(NAME_LEN))
    description: str = Column(String(255))
    currency: str = Column(String(12))
    discount: int = Column(Integer)
    tax_rate: int = Column(Integer)
    date_issued: date = Column(Date)
    due_date: date = Column(Date)

    month: str = Column(String(NAME_LEN))
    rental_amount: int = Column(Integer)
    charge_ids: str = Column(Text)
    invoice_sent: bool = Column(Boolean, default=False)
    invoice_printed: bool = Column(Boolean, default=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self) -> dict[str, str | date | int | list[str] | Customer | list[InvoicedItems]]:
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
            "charge_ids": self.charge_ids.split(",") if self.charge_ids else [],
            "invoice_items": self.invoiced_items,
            "customer": self.customer,
            "invoice_sent": self.invoice_sent,
            "invoice_printed": self.invoice_printed
        }

    @property
    def invoiced_items(self) -> list[InvoicedItems]:
        """

        :return:
        """
        with Session() as session:
            _invoiced_items = []
            for _charge_id in list(self.charge_ids.split(",")):
                charge_item_orm: UserChargesORM = session.query(UserChargesORM).filter(
                    UserChargesORM.charge_id == _charge_id).first()
                item_orm: ItemsORM = session.query(ItemsORM.item_number == charge_item_orm.item_number).first()
                invoice_item_dict = dict(property_id=charge_item_orm.property_id,
                                         item_number=charge_item_orm.item_number,
                                         description=item_orm.description, multiplier=item_orm.multiplier,
                                         amount=charge_item_orm.amount)

                _invoiced_items.append(InvoicedItems(**invoice_item_dict))
            return _invoiced_items

    @property
    def customer(self) -> Customer:
        """

        :return:
        """
        with Session() as session:
            _tenant: TenantORM = session.query(TenantORM).filter(TenantORM.tenant_id == self.tenant_id).first()
            return Customer(**_tenant.to_dict())


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
    amount: int = Column(Integer)
    date_of_entry: date = Column(Date)
    is_invoiced: bool = Column(Boolean, default=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self) -> dict[str, str | date | int | bool]:
        """
        Converts the instance attributes to a dictionary.

        :return: A dictionary representation of the instance.
        """
        return {
            "charge_id": self.charge_id,
            "property_id": self.property_id,
            "tenant_id": self.tenant_id,
            "unit_id": self.unit_id,
            "item_number": self.item_number,
            "rental_amount": self.amount,
            "date_of_entry": self.date_of_entry,
            "is_invoiced": self.is_invoiced
        }

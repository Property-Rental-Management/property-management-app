from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, inspect
from datetime import date

from sqlalchemy.orm import relationship

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


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
    amount: int = Column(Integer)
    charge_ids: list[str] = Column(Text)
    invoice_sent: bool = Column(Boolean, default=False)
    invoice_printed: bool = Column(Boolean, default=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)


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
            "amount": self.amount,
            "date_of_entry": self.date_of_entry,
            "is_invoiced": self.is_invoiced
        }

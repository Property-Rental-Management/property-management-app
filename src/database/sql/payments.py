from datetime import date

from sqlalchemy import Column, String, Date, Boolean, Integer, inspect
from sqlalchemy.ext.declarative import declarative_base

from src.database.constants import ID_LEN
from src.database.sql import engine

Base = declarative_base()


class PaymentORM(Base):
    __tablename__ = 'payments'

    transaction_id: str = Column(String(ID_LEN), primary_key=True)
    invoice_number: int = Column(String(ID_LEN))
    tenant_id: str = Column(String(ID_LEN))
    property_id: str = Column(String(ID_LEN))
    unit_id: str = Column(String(ID_LEN))
    amount_paid: int = Column(Integer)
    date_paid: date = Column(Date)
    payment_method: str = Column(String(32))
    is_successful: bool = Column(Boolean, default=False)
    month: int = Column(Integer)
    comments: str = Column(String(255))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'invoice_number': self.invoice_number,
            'tenant_id': self.tenant_id,
            'property_id': self.property_id,
            'amount_paid': self.amount_paid,
            'date_paid': self.date_paid,
            'payment_method': self.payment_method,
            'is_successful': self.is_successful,
            'month': self.month,
            'unit_id': self.unit_id,
            'comments': self.comments
        }

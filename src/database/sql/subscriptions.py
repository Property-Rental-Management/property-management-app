from datetime import date

from sqlalchemy import Column, String, Integer, Date, inspect, Boolean

from src.database.constants import ID_LEN
from src.database.sql import Base, engine


class PlansORM(Base):
    __tablename__ = "subscription_plans"
    plan_id: str = Column(String(ID_LEN), primary_key=True)
    name: str = Column(String(12))
    description: str = Column(String(255))
    price: int = Column(Integer)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "price": self.price
        }


class SubscriptionsORM(Base):
    __tablename__ = "subscriptions"
    subscription_id: str = Column(String(ID_LEN), primary_key=True)
    user_id: str = Column(String(ID_LEN))
    plan_id: str = Column(String(ID_LEN))
    date_subscribed: date = Column(Date)
    subscription_period_in_month: int = Column(Integer)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "subscription_id": self.subscription_id,
            "plan_id": self.plan_id,
            "date_subscribed": self.date_subscribed.isoformat(),
            "subscription_period_in_month": self.subscription_period_in_month
        }


class PaymentReceiptORM(Base):
    __tablename__ = "client_payment_receipt"
    receipt_id: int = Column(String(ID_LEN), primary_key=True)
    reference: str = Column(String(8))
    subscription_id: str = Column(String(ID_LEN))
    user_id: str = Column(String(ID_LEN))
    payment_amount: int = Column(Integer)
    date_created: date = Column(Date)
    payment_method: str = Column(String(16), default="direct_deposit")
    amount_paid: int = Column(Integer, nullable=True)
    date_paid: date = Column(Date, nullable=True)
    is_verified: bool = Column(Boolean, default=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self):
        return {
            "receipt_id": self.receipt_id,
            "reference": self.reference,
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "payment_amount": self.payment_amount,
            "date_created": self.date_created,
            "payment_method": self.payment_method,
            "amount_paid": self.amount_paid,
            "date_paid": self.date_paid,
            "is_verified": self.is_verified
        }

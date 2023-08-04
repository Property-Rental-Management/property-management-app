from datetime import date

from sqlalchemy import Column, String, Integer, Date, inspect

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

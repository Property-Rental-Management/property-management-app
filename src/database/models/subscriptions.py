import uuid
from datetime import date
from enum import Enum

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field


class PlanName(str, Enum):
    trial = "Trial"
    basic = "Basic"
    premium = "Premium"
    ultimate = "Ultimate"


class Plan(BaseModel):
    plan_id: str
    name: str
    price: int


class CreatePlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: int


class Subscriptions(BaseModel):
    user_id: str
    subscription_id: str
    plan: Plan
    date_subscribed: date
    subscription_period_in_month: int

    @property
    def expiry_date(self) -> date:
        """
        Calculate the expiry date based on the subscription period.
        :return: Expiry date
        """
        return self.date_subscribed + relativedelta(months=self.subscription_period_in_month)

    @property
    def is_expired(self) -> bool:
        """
        Check if the subscription is expired.
        :return: True if expired, False otherwise
        """
        return self.expiry_date < date.today()

    @property
    def is_active(self) -> bool:
        """
        Check if the subscription is currently active.
        :return: True if active, False otherwise
        """
        return not self.is_expired

    def renew_subscription(self, months: int):
        """
        Renew the subscription for the specified number of months.
        :param months: Number of months to extend the subscription
        """
        self.subscription_period_in_month += months

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
    paypal_id: str
    name: str
    description: str
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
    is_paid: bool = Field(default=False)

    def orm_dict(self) -> dict[str, str | int | date]:
        """
        :return:
        """
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "plan_id": self.plan.plan_id,
            "date_subscribed": self.date_subscribed,
            "subscription_period_in_month": self.subscription_period_in_month

        }

    def disp_dict(self) -> dict[str, str | int | date]:
        dict_ = self.dict()
        dict_.update(dict(expiry_date=self.expiry_date, payment_amount=self.payment_amount,
                          is_active=self.is_active))
        return dict_

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
        # TODO - check if all payments are made in full
        return (not self.is_expired) and self.is_paid

    @property
    def payment_amount(self) -> int:
        return self.plan.price * self.subscription_period_in_month

    def renew_subscription(self, months: int):
        """
        Renew the subscription for the specified number of months.
        :param months: Number of months to extend the subscription
        """
        self.subscription_period_in_month += months


class PaymentReceipts(BaseModel):
    """
        Direct Deposit Payments for Client Subscriptions
    """
    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reference: str
    subscription_id: str
    user_id: str
    payment_amount: int
    date_created: date
    payment_method: str = Field(default="direct_deposit")
    amount_paid: int | None
    date_paid: date | None
    is_verified: bool = Field(default=False)

    @property
    def paid_in_full(self) -> bool:
        """
        Check if the payment has been paid in full.
        :return: True if payment is fully paid, False otherwise.
        """
        if self.amount_paid is None:
            return False
        return self.amount_paid >= self.payment_amount

    @property
    def balance(self) -> int:
        """
        Calculate the remaining balance for the payment.
        :return: Remaining balance.
        """
        if self.amount_paid is None:
            return self.payment_amount

        return self.payment_amount - self.amount_paid


class SubscriptionFormInput(BaseModel):
    user_id: str
    subscription_status: str
    subscription_plan: str
    period: int
    payment_method: str

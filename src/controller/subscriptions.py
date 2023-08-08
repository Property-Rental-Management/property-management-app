import datetime
import uuid

from flask import Flask

from src.controller import Controllers, error_handler
from src.database.models.subscriptions import Subscriptions, Plan, SubscriptionFormInput, PaymentReceipts
from src.database.sql.subscriptions import SubscriptionsORM, PlansORM, PaymentReceiptORM


async def create_payment_reference():
    reference = str(uuid.uuid4())[0:8].upper()
    return reference


class SubscriptionController(Controllers):
    """

    """

    def __init__(self):
        super().__init__()
        self.subscriptions: dict[str, Subscriptions] = {}
        self.plans: list[Plan] = []
        self.payment_receipts: list[PaymentReceipts] = []

    def create_sub_model(self, sub_orm: SubscriptionsORM):
        _plan = None
        for plan in self.plans:
            if plan.plan_id == sub_orm.plan_id:
                _plan = plan

        self.logger.info(f"Plan : {_plan}")

        return self.set_active(
            subscription=Subscriptions(user_id=sub_orm.user_id, subscription_id=sub_orm.subscription_id, plan=_plan,
                                       date_subscribed=sub_orm.date_subscribed,
                                       subscription_period_in_month=sub_orm.subscription_period_in_month))

    def _load_subscriptions(self):
        """

        :return:
        """
        with self.get_session() as session:
            plans_orm_list: list[PlansORM] = session.query(PlansORM).all()
            self.plans = [Plan(**plan_orm.to_dict()) for plan_orm in plans_orm_list]
            self.logger.info(f"Plans logger : {self.plans}")

            subscriptions_orm_list: list[SubscriptionsORM] = session.query(SubscriptionsORM).all()
            self.subscriptions = {sub_orm.user_id: self.create_sub_model(sub_orm=sub_orm)
                                  for sub_orm in subscriptions_orm_list}
            payments_orm_list: list[PaymentReceiptORM] = session.query(PaymentReceiptORM).all()
            self.payment_receipts = [PaymentReceipts(**receipt.to_dict()) for receipt in payments_orm_list if
                                     receipt] if payments_orm_list else []

            self.logger.info(f"Subscriptions Logger: {self.subscriptions}")

    def init_app(self, app: Flask):
        self._load_subscriptions()

    @error_handler
    async def get_subscription_by_uid(self, user_id: str) -> Subscriptions | None:
        """

        :param user_id:
        :return:
        """
        if user_id in self.subscriptions:
            return self.subscriptions.get(user_id)

        with self.get_session() as session:
            subscription_orm = session.query(SubscriptionsORM).filter(SubscriptionsORM.user_id == user_id).first()
            if not subscription_orm:
                return None

            subscription = Subscriptions(**subscription_orm.to_dict())
            self.subscriptions[subscription.user_id] = subscription
            return subscription

    @error_handler
    async def get_plan_by_id(self, plan_id: str) -> Plan | None:
        """
        """
        for plan in self.plans:
            if plan.plan_id == plan_id:
                return plan

        with self.get_session() as session:
            plan_orm = session.query(PlansORM).filter(PlansORM.plan_id == plan_id).first()
            if not plan_orm:
                return None

            return Plan(**plan_orm.to_dict())

    @error_handler
    async def get_subscriptions_by_plan_name(self, plan_name: str) -> list[Subscriptions]:
        """

        :param plan_name:
        :return:
        """

        return [subscription for subscription in self.subscriptions.values()
                if subscription.plan.name.casefold() == plan_name.casefold()]

    @error_handler
    async def add_subscription_plan(self, plan: Plan) -> Plan:
        """

        :param plan:
        :return:
        """
        with self.get_session() as session:
            plan_orm = PlansORM(**plan.dict())
            session.add(plan_orm)
            session.commit()
            self.plans.append(plan)
            return plan

    @error_handler
    async def create_new_subscription(self, subscription_form: SubscriptionFormInput):
        # Create Payment Data  depending on selected payment options
        # display payment screen depending on selected payment options
        # return the proper payment form or payment information form
        # depending on the payment form then display the appropriate response
        plan = await self.get_plan_by_id(plan_id=subscription_form.subscription_plan)
        new_subscription = Subscriptions(user_id=subscription_form.user_id,
                                         subscription_id=str(uuid.uuid4()),
                                         plan=plan,
                                         date_subscribed=datetime.datetime.now().date(),
                                         subscription_period_in_month=subscription_form.period,
                                         subscription_activated=False)

        if subscription_form.payment_method == "direct_deposit":
            # Perform cash payment related tasks such as creating a cash payment receipt with its model and reference
            # save this model in the database then return the information to the user

            reference = await create_payment_reference()
            payment_receipt = PaymentReceipts(reference=reference, subscription_id=new_subscription.subscription_id,
                                              user_id=subscription_form.user_id,
                                              payment_amount=new_subscription.payment_amount,
                                              date_created=datetime.datetime.now().date(),
                                              payment_method=subscription_form.payment_method)

            with self.get_session() as session:
                session.add(SubscriptionsORM(**new_subscription.orm_dict()))
                session.add(PaymentReceiptORM(**payment_receipt.dict()))
                session.commit()

            return dict(subscription=new_subscription.disp_dict(), payment=payment_receipt.dict())

        elif subscription_form.payment_method == "paypal":
            pass

    @error_handler
    async def reprint_payment_details(self, subscription_id: str):
        """

        :param subscription_id:
        :return:
        """
        with self.get_session() as session:
            subscription_orm = session.query(SubscriptionsORM).filter(
                SubscriptionsORM.subscription_id == subscription_id).first()
            payment_orm = session.query(PaymentReceiptORM).filter(
                PaymentReceiptORM.subscription_id == subscription_id).first()
            subscription = self.create_sub_model(subscription_orm)
            payment_receipt = PaymentReceipts(**payment_orm.to_dict())
            self.logger.info(f"Subscription : {subscription}")
            self.logger.info(f"Payment Receipt: {payment_receipt}")
            return dict(subscription=subscription.disp_dict(), payment=payment_receipt.dict())

    def subscription_is_paid(self, subscription_id: str) -> bool:
        """
        """
        for receipt in self.payment_receipts:
            if receipt.subscription_id == subscription_id:
                return receipt.paid_in_full
        return False

    def set_active(self, subscription: Subscriptions) -> Subscriptions:
        subscription.is_paid = self.subscription_is_paid(subscription_id=subscription.subscription_id)
        return subscription

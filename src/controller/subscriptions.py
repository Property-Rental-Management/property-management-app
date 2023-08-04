from flask import Flask

from src.controller import Controllers, error_handler
from src.database.models.subscriptions import Subscriptions, Plan
from src.database.sql.subscriptions import SubscriptionsORM, PlansORM


class SubscriptionController(Controllers):
    """

    """

    def __init__(self):
        super().__init__()
        self.subscriptions: dict[str, Subscriptions] = {}
        self.plans: list[Plan] = []

    def _load_subscriptions(self):
        """

        :return:
        """
        with self.get_session() as session:
            subscriptions_orm_list: list[SubscriptionsORM] = session.query(SubscriptionsORM).all()
            plans_orm_list: list[PlansORM] = session.query(PlansORM).all()
            self.subscriptions = {sub_orm.user_id: Subscriptions(**sub_orm.to_dict())
                                  for sub_orm in subscriptions_orm_list}
            self.plans = [Plan(**plan_orm.to_dict()) for plan_orm in plans_orm_list]

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
    async def get_subscriptions_by_plan_name(self, plan_name: str) -> list[Subscriptions]:
        """

        :param plan_name:
        :return:
        """

        return [subscription for subscription in self.subscriptions.values()
                if subscription.plan.name.casefold() == plan_name.casefold()]

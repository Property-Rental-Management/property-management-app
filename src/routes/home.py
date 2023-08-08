from flask import Blueprint, render_template

from src.authentication import user_details
from src.database.models.notifications import NotificationsModel
from src.database.models.users import User
from src.main import notifications_controller, subscriptions_controller

home_route = Blueprint('home', __name__)


@home_route.get('/')
@user_details
async def get_home(user: User):
    """
    :param user:
    :return:
    """
    plans_list = [plan.dict() for plan in subscriptions_controller.plans]
    context = dict(plans_list=plans_list)
    if user:
        notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)
        notifications_dicts = [notice.dict() for notice in notifications.unread_notification if notice] if notifications else []
        subscription = await subscriptions_controller.get_subscription_by_uid(user_id=user.user_id)
        context.update(dict(
            user=user.dict(), notifications_list=notifications_dicts,
            subscription=subscription.disp_dict() if subscription else {}))
    return render_template('index.html', **context)

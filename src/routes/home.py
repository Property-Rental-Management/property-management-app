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
    if user:
        user_data = user.dict()
        notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)
        notifications_dicts = [notice.dict() for notice in notifications.unread_notification if notice] if notifications else []
        plans_list = [plan.dict() for plan in subscriptions_controller.plans]
        context = dict(user=user_data,
                       notifications_list=notifications_dicts,
                       plans_list=plans_list)

    else:
        context = {}
    return render_template('index.html', **context)

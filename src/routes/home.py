from flask import Blueprint, render_template, send_from_directory

from src.authentication import user_details
from src.database.models.notifications import NotificationsModel
from src.database.models.users import User
from src.main import notifications_controller, subscriptions_controller
from src.utils import static_folder

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
        notifications_dicts = [notice.dict() for notice in notifications.unread_notification if
                               notice] if notifications else []
        subscription = await subscriptions_controller.get_subscription_by_uid(user_id=user.user_id)
        context.update(dict(
            user=user.dict(), notifications_list=notifications_dicts,
            subscription=subscription.disp_dict() if subscription else {}))
    return render_template('index.html', **context)


@home_route.get('/faq')
@user_details
async def get_faq(user: User):
    """

    :param user:
    :return:
    """
    context = {}
    return render_template('faq.html', **context)


@home_route.get('/about')
@user_details
async def get_about(user: User):
    """

    :param user:
    :return:
    """
    context = {}
    return render_template('about.html', **context)


@home_route.get('/sister-sites')
@user_details
async def get_sites(user: User):
    """

    :param user:
    :return:
    """
    context = {}
    return render_template('sites.html', **context)


@home_route.get('/robots.txt')
def robots_txt():
    return send_from_directory(static_folder(), 'robots.txt')


@home_route.get('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(static_folder(), 'sitemap.xml')

from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.profile import ProfileUpdate
from src.database.models.users import User, UserUpdate
from src.logger import init_logger
from src.main import user_controller, subscriptions_controller

admin_logger = init_logger('admin_logger')
profile_routes = Blueprint('profile', __name__)


@profile_routes.get('/dashboard/profile')
@login_required
async def get_profile(user: User):
    """
        **get_profile**

    :param user:
    :return:
    """
    profile = await user_controller.get_profile_by_user_id(user_id=user.user_id)
    profile_dict = profile.dict() if profile else {}

    subscription = await subscriptions_controller.get_subscription_by_uid(user_id=user.user_id)
    subscription_dict = subscription.dict() if subscription else {}
    subscription_plans = [plan.dict() for plan in subscriptions_controller.plans]
    context = dict(user=user.dict(),
                   profile=profile_dict,
                   subscription=subscription_dict,
                   plan_list=subscription_plans)

    return render_template('profile/profile.html', **context)


@profile_routes.post('/dashboard/profile')
@login_required
async def update_profile(user: User):
    """
        **update_profile**
    :param user:
    :return:
    """
    try:
        user_update = UserUpdate(**request.form)
        profile_update = ProfileUpdate(**request.form)
        admin_logger.info(f"Profile : {profile_update} , User: {user_update}")
    except ValidationError as e:
        admin_logger.error(str(e))
        flash(message="Unable to update profile", category="danger")
        return redirect(url_for('profile.get_profile'), code=302)

    _ = await user_controller.update_profile(user=user_update, profile=profile_update)
    flash(message="Successfully updated Profile", category="success")
    return redirect(url_for('profile.get_profile'), code=302)


@profile_routes.get('/dashboard/subscribe/<string:plan_id>')
@login_required
async def subscribe_link(user: User, plan_id: str):
    """

    :param user:
    :param plan_id:
    :return:
    """
    print(f"Plan ID : {plan_id}")

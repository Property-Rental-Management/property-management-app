import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.profile import ProfileUpdate
from src.database.models.subscriptions import SubscriptionFormInput
from src.database.models.users import User, UserUpdate
from src.logger import init_logger
from src.main import user_controller, subscriptions_controller

admin_logger = init_logger('admin_logger')
profile_routes = Blueprint('profile', __name__)


async def create_payment_reference():
    reference = str(uuid.uuid4())[0:8].upper()
    return reference


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
    subscription_dict = subscription.disp_dict() if subscription else {}
    subscription_plans = [plan.dict() for plan in subscriptions_controller.plans]
    context = dict(user=user.dict(),
                   profile=profile_dict,
                   subscription=subscription_dict,
                   plan_list=subscription_plans)

    admin_logger.info(f"Subscription in view : {subscription_dict}")

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


@profile_routes.post('/dashboard/subscribe')
@login_required
async def subscribe_link(user: User):
    """

    :param user:
    :return:
    """
    try:
        subscription_form = SubscriptionFormInput(**request.form)
    except ValidationError as e:
        admin_logger.error(f"Error Subscribing : {str(e)}")
        flash(message="Unable to Subscribe", category="danger")
        return redirect(url_for('profile.get_profile'))
    # Create Payment Data  depending on selected payment options
    # display payment screen depending on selected payment options
    # return the proper payment form or payment information form
    # depending on the payment form then display the appropriate response
    if subscription_form.payment_method == "direct_deposit":
        # Perform cash payment related tasks such as creating a cash payment receipt with its model and reference
        # save this model in the database then return the information to the user
        context = await subscriptions_controller.create_new_subscription(subscription_form=subscription_form)
        return render_template("profile/payments/direct_deposit.html", **context)

    elif subscription_form.payment_method == "paypal":
        context = await subscriptions_controller.create_new_subscription(subscription_form=subscription_form)
        return render_template("profile/payments/paypal.html", **context)


@profile_routes.get('/dashboard/subscription-payment/<string:subscription_id>')
@login_required
async def reprint_payment_details(user: User, subscription_id: str):
    admin_logger.info(f"Subscription ID : {subscription_id}")
    context = await subscriptions_controller.reprint_payment_details(subscription_id=subscription_id)
    admin_logger.info(f"Admin Logger : {context}")
    return render_template("profile/payments/direct_deposit.html", **context)


@profile_routes.get('/dashboard/plan-data/<string:plan_id>')
@login_required
async def get_plan_details(user: User, plan_id: str):
    """

    :param user:
    :param plan_id:
    :return:
    """
    plan = await subscriptions_controller.get_plan_by_id(plan_id=plan_id)

    return plan.dict() if plan else {}

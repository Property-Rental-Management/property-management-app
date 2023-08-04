from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import admin_login
from src.database.models.subscriptions import PlanName, CreatePlan, Plan
from src.database.models.users import User
from src.logger import init_logger
from src.main import user_controller, tenant_controller, company_controller, subscriptions_controller

admin_logger = init_logger('admin_logger')
admin_routes = Blueprint('admin', __name__)


@admin_routes.get('/admin')
@admin_login
async def get_admin(user: User):
    """
        **get_admin**

    :param user:
    :return:
    """
    plans = subscriptions_controller.plans
    subscribers = subscriptions_controller.subscriptions
    plans_dict = [plan.dict() for plan in plans]
    subscription_dicts = [subscription.dict() for subscription in subscribers.values()]
    plan_types = [plan_type.value for plan_type in PlanName]
    context = dict(user=user.dict(),
                   plans=plans_dict,
                   subscriptions=subscription_dicts,
                   plan_types=plan_types)

    return render_template('admin/admin.html', **context)


@admin_routes.post('/admin/subscription/create')
@admin_login
async def add_subscription_plan(user: User):
    """
        **add_subscription_plan**

    :return:
    """
    try:
        subscription_plan = CreatePlan(**request.form)
        admin_logger.info(f"Subscription Plan : {subscription_plan}")
    except ValidationError as e:
        admin_logger.error(f"Error : {str(e)}")
        flash(message="Error creating subscription plan", category='danger')
        return redirect(url_for('admin.get_admin'), code=302)

    if subscription_plan:
        plan: Plan = Plan(**subscription_plan.dict())
        _ = await subscriptions_controller.add_subscription_plan(plan=plan)

        flash(message="Successfully created new plan", category="success")
    return redirect(url_for('admin.get_admin'), code=302)


@admin_routes.get('/admin/users')
@admin_login
async def get_users(user: User):
    """

    :param user:
    :return:
    """
    users = user_controller.users
    _users = [user.dict() for user in users.values()]
    admin_logger.info(f"Admin Logger : {_users}")
    context = dict(user=user.dict(), users=_users)

    return render_template('admin/users.html', **context)


@admin_routes.get('/admin/user/<string:user_id>')
@admin_login
async def admin_get_user(user: User, user_id: str):
    """
        **admin_get_user**
    :param user_id:
    :param user:
    :return:
    """
    data_user = await user_controller.get(user_id=user_id)
    context = dict(user=user.dict(), data=dict(user=data_user.dict()))
    return render_template('admin/users/user.html', **context)


@admin_routes.get('/admin/tenants')
@admin_login
async def get_tenants(user: User):
    """

    :param user:
    :return:
    """
    tenants = [tenant.dict() for tenant in tenant_controller.tenants]
    context = dict(user=user.dict(), tenants=tenants)
    return render_template('admin/tenants.html', **context)


@admin_routes.get('/admin/companies')
@admin_login
async def admin_get_companies(user: User):
    """

    :param user:
    :return:
    """
    companies = [company.dict() for company in company_controller.companies]
    admin_logger.info(f"Admin logger : {companies}")
    context = dict(user=user.dict(), companies=companies)
    return render_template('admin/companies.html', **context)


@admin_routes.get('/admin/buildings')
@admin_login
async def admin_get_buildings(user: User):
    """

    :param user:
    :return:
    """
    buildings = [building.dict() for building in company_controller.buildings]
    admin_logger.info(f"Admin logger : {buildings}")
    context = dict(user=user.dict(), buildings=buildings)
    return render_template('admin/buildings.html', **context)

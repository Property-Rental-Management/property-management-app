from flask import Blueprint, render_template

from flask import Blueprint, render_template

from src.authentication import admin_login
from src.database.models.users import User
from src.logger import init_logger
from src.main import user_controller

admin_logger = init_logger('admin_logger')
admin_routes = Blueprint('admin', __name__)


@admin_routes.get('/admin')
@admin_login
async def get_admin(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user.dict())
    return render_template('admin/admin.html', **context)


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
    context = dict(user=user.dict())
    return render_template('admin/tenants.html', **context)

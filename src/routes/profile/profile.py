from flask import Blueprint, render_template

from src.authentication import login_required
from src.database.models.users import User
from src.logger import init_logger
from src.main import user_controller

admin_logger = init_logger('admin_logger')
profile_routes = Blueprint('profile', __name__)


@profile_routes.get('/dashboard/profile')
@login_required
async def get_profile(user: User):
    """

    :param user:
    :return:
    """
    profile = await user_controller.get_profile(user_id=user.user_id)
    profile = profile.dict() if profile else {}
    context = dict(user=user.dict(), profile=profile)
    return render_template('profile/profile.html', **context)


@profile_routes.post('/dashboard/profile')
@login_required
async def update_profile(user: User):
    """

    :param user:
    :return:
    """
    profile = await user_controller.get_profile(user_id=user.user_id)
    profile = profile.dict() if profile else {}
    context = dict(user=user.dict(), profile=profile)
    return render_template('profile/profile.html', **context)

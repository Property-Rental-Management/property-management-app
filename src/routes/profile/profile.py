from flask import Blueprint, render_template

from src.authentication import login_required
from src.database.models.users import User
from src.logger import init_logger

admin_logger = init_logger('admin_logger')
profile_routes = Blueprint('profile', __name__)


@profile_routes.get('/dashboard/profile')
@login_required
async def get_profile(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user.dict())
    return render_template('profile/profile.html', **context)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.profile import ProfileUpdate
from src.database.models.users import User, UserUpdate
from src.logger import init_logger
from src.main import user_controller

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
    profile = await user_controller.get_profile(user_id=user.user_id)
    profile = profile.dict() if profile else {}
    context = dict(user=user.dict(), profile=profile)
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

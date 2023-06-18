from flask import Blueprint, render_template

from src.database.models.users import User
from src.authentication import login_required

buildings_route = Blueprint('buildings', __name__)


@buildings_route.get('/admin/buildings')
@login_required
async def get_buildings(user: User):

    user_data = user.dict()
    context = dict(user=user_data)
    # TODO load company data based on user data
    return render_template('building/buildings.html', **context)


@buildings_route.get('/admin/building/<string:building_id>')
@login_required
async def get_building(user: User, building_id: str):
    """
        returns a specific building by building id
    :param user:
    :param building_id:
    :return:
    """
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('building/building.html', **context)


@buildings_route.get('/admin/add-building')
@login_required
async def add_building(user: User):
    user_data = user.dict()
    context = dict(user=user_data)
    # TODO load company data based on user data

    return render_template('building/add_building.html', **context)

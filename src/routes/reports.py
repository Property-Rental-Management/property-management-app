

from flask import Blueprint, render_template

from src.authentication import login_required
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller

reports_route = Blueprint('reports', __name__)

report_logger = init_logger('REPORT LOGGER:')


@reports_route.get('/admin/reports')
@login_required
async def get_reports(user: User):
    user_data = user.dict()
    companies = await company_controller.get_user_companies(user_id=user.user_id)
    companies_dicts = [company.dict() for company in companies if company] if companies else []
    context = dict(user=user_data, companies=companies_dicts)

    return render_template('reports/reports.html', **context)

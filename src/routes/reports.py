import plotly.graph_objects as plot
from flask import Blueprint, render_template, request, redirect, url_for, flash

from src.authentication import login_required
from src.database.models.cashflow import CashFlowModel
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller

reports_route = Blueprint('reports', __name__)

report_logger = init_logger('REPORT_LOGGER:')


async def create_bar_graph(cashflows: dict, user: User, company_id: str, title: str, x_title: str):
    """
        **create_bar_graph**
    :param cashflows:
    :param company_id:
    :param user:
    :param title:
    :param x_title:
    :return:
    """
    company = await company_controller.get_company_internal(company_id=company_id)
    x_axis = [month for month, cashflow in enumerate(cashflows.values())]
    # x_axis = ["January", "February", "March", "April"]
    y_axis = [cashflow.cashflow for month, cashflow in enumerate(cashflows.values())]
    # y_axis = [50000, 120000, 450000, 956000]
    figure = plot.Figure(data=plot.Bar(x=x_axis, y=y_axis))
    figure.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title="Income",
        showlegend=True
    )
    context = dict(user=user.dict(), company=company.dict(), chart_data=figure.to_json())
    return context


async def monthly_cashflow_context(company_id: str, user: User):
    """
        **monthly_cashflow_context**
    :param company_id:
    :param user:
    :return:
    """

    cashflow = CashFlowModel(company_id=company_id)
    report_logger.info(f"cashflow : {cashflow}")
    cashflows = await cashflow.monthly_cashflow()
    return await create_bar_graph(cashflows=cashflows, company_id=company_id, user=user,
                                  title="Monthly Cashflow", x_title="Month")


async def property_cashflow_context(company_id: str, user: User):
    """
        **property_cashflow_context**
    :param company_id:
    :param user:
    :return:
    """
    cashflow = CashFlowModel(company_id=company_id)
    report_logger.info(f"cashflow : {cashflow}")
    cashflows = await cashflow.monthly_cashflow_by_property()
    return await create_bar_graph(cashflows=cashflows, company_id=company_id, user=user, title="Property Cashflow",
                                  x_title="Property")


@reports_route.get('/admin/reports')
@login_required
async def get_reports(user: User):
    user_data = user.dict()
    companies = await company_controller.get_user_companies(user_id=user.user_id)
    companies_dicts = [company.dict() for company in companies if company] if companies else []
    context = dict(user=user_data, companies=companies_dicts)

    return render_template('reports/reports.html', **context)


@reports_route.get('/admin/report/<string:company_id>')
@login_required
async def report(user: User, company_id: str):
    """
        **report**
    :param user:
    :param company_id:
    :return:
    """
    context = await monthly_cashflow_context(company_id=company_id, user=user)
    context.update(dict(selected="monthly_cashflow"))
    return render_template('reports/reporting_interface.html', **context)


@reports_route.post('/admin/report/monthly-cashflow/<string:company_id>')
@login_required
async def select_cashflow(user: User, company_id: str):
    """

    :param user:
    :param company_id:
    :return:
    """
    cashflow_type = request.form.get('cashflow_type')
    report_logger.info(f"Cashflow Type :  {cashflow_type}")
    if cashflow_type is None:
        message: str = f"please select cashflow report to display"
        flash(message=message, category="danger")
        return redirect(url_for('reports.report', company_id=company_id), code=302)

    if cashflow_type == "monthly_cashflow":

        context = await monthly_cashflow_context(company_id=company_id, user=user)
        context.update(dict(selected="monthly_cashflow"))
        return render_template('reports/reporting_interface.html', **context)

    elif cashflow_type == "cashflow_by_property":
        context = await property_cashflow_context(company_id=company_id, user=user)
        context.update(dict(selected="cashflow_by_property"))
        return render_template('reports/reporting_interface.html', **context)

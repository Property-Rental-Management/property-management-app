import plotly.graph_objects as plot
from flask import Blueprint, render_template, request, redirect, url_for, flash

from src.authentication import login_required
from src.database.models.cashflow import CashFlowModel
from src.database.models.properties import Property
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller

reports_route = Blueprint('reports', __name__)

report_logger = init_logger('REPORT_LOGGER:')


async def get_company_name(property_id: str) -> str:
    building: Property = await company_controller.get_property_by_id_internal(property_id=property_id)
    return building.name if building else None


async def months_names(year: int, month: int) -> str:
    """
        **months_names**
    :param year:
    :param month:
    :return:
    """
    months = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
              7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}

    return f"{year}-{months.get(month, '')}"


async def create_bar_graph(cashflows: dict, user: User, company_id: str, flow_type: str = "monthly"):
    """
        **create_bar_graph**
    :param flow_type:
    :param cashflows:
    :param company_id:
    :param user:
    :return:
    """
    color_pallet = ['rgb(31, 119, 180)', 'rgb(255, 127, 14)', 'rgb(44, 160, 44)', 'rgb(214, 39, 40)',
                    'rgb(148, 103, 189)', 'rgb(140, 86, 75)', 'rgb(227, 119, 194)', 'rgb(127, 127, 127)',
                    'rgb(188, 189, 34)', 'rgb(23, 190, 207)']

    company = await company_controller.get_company_internal(company_id=company_id)
    if flow_type.casefold() == "monthly":
        title = "Monthly Cashflow"
        x_title = "Month"
        x_axis = [await months_names(year=cashflow.year, month=cashflow.month) for cashflow in cashflows.values()]
        y_axis = [cashflow.cashflow for cashflow in cashflows.values()]

    elif flow_type.casefold() == "property":
        title = "Property Cashflow"
        x_title = "Property"
        x_axis = [await get_company_name(property_id=cashflow.property_id) for cashflow in cashflows.values()]
        y_axis = [cashflow.cashflow for cashflow in cashflows.values()]

    else:
        return None

    report_logger.info(f"y_axis : {y_axis}")
    report_logger.info(f"x_axis : {x_axis}")

    figure = plot.Figure(data=plot.Bar(x=x_axis, y=y_axis, marker=dict(color=color_pallet)))
    figure.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title="Income",
        showlegend=True
    )

    return dict(user=user.dict(), company=company.dict(), chart_data=figure.to_json())


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
    return await create_bar_graph(cashflows=cashflows, company_id=company_id, user=user, flow_type="monthly")


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
    return await create_bar_graph(cashflows=cashflows, company_id=company_id, user=user, flow_type="property")


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

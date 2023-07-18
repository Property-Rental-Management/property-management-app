from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.statements import CreateStatement, StatementForm
from src.database.models.users import User
from src.logger import init_logger

statement_logger = init_logger('statement_logger')

statements_route = Blueprint('statements', __name__)


@statements_route.get('/admin/statements')
@login_required
async def get_statements(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('statements/statements.html', **context)


@statements_route.post('/admin/statement/create')
@login_required
async def create_statement(user: User):
    """

    :param user:
    :return:
    """
    tenant_id = request.form.get('tenant_id')
    try:
        statement: StatementForm = StatementForm(**request.form)
        statement_logger.info(f"Statement : {statement}")
    except ValidationError as e:
        statement_logger.error(str(e))
        return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id))

    period: tuple[date, date] = statement.start_date, statement.end_date
    statement_instance: CreateStatement = CreateStatement(tenant_id=statement.tenant_id, statement_period=period)
    year, month = statement.start_date.year, statement.start_date.month
    new_statement = await statement_instance.create_month_statement(year=year, month=month)
    statement_logger.info(new_statement.dict())
    context = dict(statement=new_statement.dict())
    return render_template("statements/statement.html", **context)

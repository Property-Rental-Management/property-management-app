import asyncio
import logging

from flask import Blueprint, render_template, request, url_for, redirect, flash, send_file
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.bank_accounts import BusinessBankAccount
from src.database.models.companies import Company, UpdateCompany, CreateTenantRelationCompany, \
    TenantRelationCompany, CreateTenantCompany, UpdateTenantCompany, CreateCompany
from src.database.models.notifications import NotificationsModel
from src.database.models.properties import Property
from src.database.models.users import User
from src.logger import init_logger
from src.main import notifications_controller, company_controller, tenant_controller
from src.reports import create_report
from src.reports.bank_account_report import BankAccountPrintParser
from src.reports.company_report import map_company_to_parser, CompanyPrintParser

companies_route = Blueprint('companies', __name__)
companies_logger = init_logger('companies_logger')
companies_logger.setLevel(logging.INFO)


@companies_route.get('/admin/companies')
@login_required
async def get_companies(user: User):
    """

    :param user:
    :return:
    """
    context: dict[str, str | list[dict[str, str]]] = dict(user=user.dict())
    get_companies_instance = company_controller.get_user_companies(user_id=user.user_id)
    get_notifications = notifications_controller.get_user_notifications(user_id=user.user_id)
    companies, notifications = await asyncio.gather(*[get_companies_instance, get_notifications])
    companies_dict = [company.dict() for company in companies if company] if isinstance(companies, list) else []
    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []

    context.update({'companies': companies_dict, 'notifications_list': notifications_dicts})

    return render_template('companies/companies.html', **context)


@companies_route.get('/admin/company/<string:company_id>')
@login_required
async def get_company(user: User, company_id: str):
    user_data = user.dict()

    company: Company = await company_controller.get_company(company_id=company_id, user_id=user.user_id)
    company_dicts = company.dict() if company else {}

    properties: list[Property] = await company_controller.get_properties(user=user, company_id=company_id)

    bank_accounts: BusinessBankAccount = await company_controller.get_bank_accounts(user=user, company_id=company_id)
    bank_accounts_dicts = bank_accounts.dict() if isinstance(bank_accounts, BusinessBankAccount) else {}

    properties_dict = [prop.dict() for prop in properties if prop] if isinstance(properties, list) else []

    notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)
    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []

    context = dict(user=user_data,
                   company=company_dicts,
                   properties=properties_dict,
                   bank_account=bank_accounts_dicts,
                   notifications_list=notifications_dicts)

    return render_template('companies/company.html', **context)


@companies_route.get('/admin/create-company')
@login_required
async def get_create_company(user: User):
    user_data = user.dict()
    notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)

    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []

    context = dict(user=user_data, notifications_list=notifications_dicts)

    return render_template('companies/create_company.html', **context)


@companies_route.post('/admin/create-company')
@login_required
async def do_create_company(user: User):
    """
        **do_create_company**
    :param user:
    :return:
    """
    try:
        company_data = CreateCompany(**request.form)
        _company_data = await company_controller.create_company(company=company_data, user=user)
        _message = f"Company {_company_data.company_name} Added Successfully"
        flash(message=_message, category="success")
    except ValidationError as e:
        companies_logger.error(str(e))
        flash(message="Error creating Company please fill in all required fields", category='danger')

    return redirect(url_for('companies.get_companies'), code=302)


@companies_route.post('/admin/edit-company/<string:company_id>')
@login_required
async def do_edit_company(user: User, company_id: str):
    """

    :param user:
    :param company_id:
    :return:
    """
    try:
        company_data: UpdateCompany = UpdateCompany(**request.form)
    except ValidationError:
        message: str = "Error cannot update Company Data, Invalid Fields"
        flash(message=message, category="danger")
        return redirect(url_for('companies.get_company', company_id=company_id))

    _ = await company_controller.update_company(user=user, company_data=company_data)
    flash(message="Successfully Updated Company Data", category="success")
    return redirect(url_for('companies.get_company', company_id=company_id), code=302)


@companies_route.post('/admin/company/add-bank-account/<string:company_id>')
@login_required
async def do_add_bank_account(user: User, company_id: str):
    try:
        bank_account_details: BusinessBankAccount = BusinessBankAccount(**request.form)
        if company_id != bank_account_details.company_id:
            flash(message='Ouch That one hurt ', category="danger")
            return redirect(url_for('home.get_home'))

        account_details = await company_controller.update_bank_account(user=user,
                                                                       account_details=bank_account_details)

        flash(message="successfully updated company_id bank account details", category="success")
    except ValidationError as e:
        companies_logger.error(str(e))
        flash(message="Error creating Bank Account please fill in all the details", category="danger")

    return redirect(url_for('companies.get_company', company_id=company_id), code=302)


@companies_route.get('/admin/company/print/<string:company_id>')
@login_required
async def print_company(user: User, company_id: str):
    """

    :param user:
    :param company_id:
    :return:
    """
    user_id = user.user_id

    company_data: Company = await company_controller.get_company(company_id=company_id,
                                                                 user_id=user_id)
    company_bank_account: BusinessBankAccount = await company_controller.get_bank_accounts(user=user,
                                                                                           company_id=company_id)
    properties_list: list[Property] = await company_controller.get_properties(user=user,
                                                                              company_id=company_id)

    _title = f"{company_data.company_name.upper()} Report"
    # TODO - add more data points to print
    company_data: CompanyPrintParser = map_company_to_parser(company=company_data)
    company_data_dict = {}
    if company_bank_account:
        bank_account_data: BankAccountPrintParser = BankAccountPrintParser(**company_bank_account.dict())
        company_data_dict.update({"Bank Account": bank_account_data.to_dict()})

    company_data_dict.update(company_data.to_dict())
    properties_dict = [building.dict() for building
                       in properties_list if building] if isinstance(properties_list, list) else []
    company_data_dict.update({"Properties": properties_dict})

    document_buffer = create_report(title=_title, data=company_data_dict)

    return send_file(
        path_or_file=document_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{_title}.pdf")


@companies_route.post('/admin/add-tenants-company')
@login_required
async def add_tenants_company(user: User):
    """
    **add_tenants_company**


    :param user:
    :return:
    """
    building_id = request.form.get('building_id')
    unit_id = request.form.get('unit_id')
    try:
        tenant_company: CreateTenantCompany = CreateTenantCompany(**request.form)
        tenant_company_relation: CreateTenantRelationCompany = CreateTenantRelationCompany(**tenant_company.dict())
    except ValidationError as e:
        companies_logger.error(f"Error creating Tenant Company: {str(e)}")
        flash(message="Unable to add company to tenant - please check your input fields", category="danger")
        return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id), code=302)

    if tenant_company.description is None:
        tenant_company.description = "Tenant Company"

    new_company_data = await company_controller.create_company_internal(company=Company(**tenant_company.dict()))
    new_company_relation: TenantRelationCompany = await company_controller.create_company_tenant_relation_internal(
        company_relation=tenant_company_relation)

    tenant_data = await tenant_controller.get_tenant_by_id(tenant_id=tenant_company.tenant_id)
    tenant_data.company_id = tenant_company.company_id
    updated_tenant = await tenant_controller.update_tenant(tenant=tenant_data)

    flash(message="successfully created tenant company", category="success")
    return redirect(url_for('buildings.get_unit', building_id=tenant_company.building_id,
                            unit_id=tenant_company.unit_id), code=302)


@companies_route.post('/admin/update-tenant-company/<string:company_id>')
@login_required
async def update_tenant_company(user: User, company_id: str):
    """
        **update_tenant_company**
    :param user:
    :param company_id:
    :return:
    """
    tenant_company_data = UpdateTenantCompany(**request.form)
    if company_id == tenant_company_data.company_id:
        updated_company: UpdateTenantCompany | None = await company_controller.update_tenant_company(
            company_data=tenant_company_data)
    else:
        updated_company = None

    if updated_company:
        flash(message=f"Updated Tenant Company data : {updated_company.company_name}", category="success")
    else:
        flash(message=f"Unable to Update Company Data : {updated_company.company_name}", category="danger")

    _company_id = tenant_company_data.company_id or company_id
    unit_id = tenant_company_data.unit_id

    return redirect(url_for('buildings.get_unit', building_id=tenant_company_data.building_id, unit_id=unit_id),
                    code=302)

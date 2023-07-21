from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.companies import Company
from src.database.models.invoices import Invoice, PaymentStatus
from src.database.models.properties import Property, Unit
from src.database.models.tenants import QuotationForm, Tenant, CreateTenant, TenantSendMail, TenantAddress, \
    CreateTenantAddress
from src.database.models.users import User
from src.emailer import EmailModel
from src.logger import init_logger
from src.main import tenant_controller, company_controller, send_mail, lease_agreement_controller

tenants_route = Blueprint('tenants', __name__)
tenants_logger = init_logger('tenants_logger')


@tenants_route.get('/admin/tenants-list')
@login_required
async def get_tenants(user: User):
    user_data = user.dict()

    companies: list[Company] = await company_controller.get_user_companies(user_id=user.user_id)
    all_tenants = []
    for company in companies:
        tenants_list = []
        if isinstance(company, Company):
            tenants_list = await tenant_controller.get_tenants_by_company_id(company_id=company.company_id)
            tenants_logger.info(f"tenants : {tenants_list}")

        for tenant in tenants_list:
            tenant_dict = tenant.dict() if isinstance(tenant, Tenant) else None
            if tenant_dict:
                print(tenant_dict)
                all_tenants.append(tenant_dict)

    companies_dicts = [company.dict() for company in companies if company] if isinstance(companies, list) else []

    context = dict(user=user_data, companies=companies_dicts, tenants=all_tenants)
    return render_template('tenants/get_tenant.html', **context)


@tenants_route.get('/admin/tenant/buildings/<string:company_id>')
@login_required
async def get_buildings(user: User, company_id: str):
    # Query the database or perform any necessary logic to fetch the buildings based on the company_id ID

    buildings: list[Property] = await company_controller.get_properties(user=user, company_id=company_id)

    buildings_dicts = [building.dict() for building in buildings if building] if isinstance(buildings, list) else []
    # Return the buildings as JSON response
    return jsonify(buildings_dicts)


@tenants_route.post('/admin/add-tenants/<string:building_id>/<string:unit_id>')
@login_required
async def do_add_tenants(user: User, building_id: str, unit_id: str):
    """
        **do_add_tenants**
        :param user:
        :param building_id:
        :param unit_id:
        :return:
    """
    user_data = user.dict()
    new_tenant = CreateTenant(**request.form)
    tenant_added = await tenant_controller.create_tenant(user_id=user.user_id, tenant=new_tenant)
    flash(message="Tenant Successfully added - Continue to create a lease for tenant", category='success')
    return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id), code=302)


@tenants_route.post('/admin/tenant-rentals')
@login_required
async def tenant_rentals(user: User):
    user_data = user.dict()
    tenant_quote: QuotationForm = QuotationForm(**request.form)
    quotation = await tenant_controller.create_quotation(user=user, quotation=tenant_quote)

    message = """Quote Created and Notification will be sent, via email or cell. 
    
    Lease Agreements and a Quotation will be sent via email &
    Remember you can Reprint Both the Quotation & Lease Agreement from the Tenant Details Section
    """

    flash(message=message, category="success")
    return redirect(url_for('tenants.get_tenants'), code=302)


# noinspection DuplicatedCode
@tenants_route.get('/admin/tenant/<string:tenant_id>')
@login_required
async def get_tenant(user: User, tenant_id: str):
    """

    :param user:
    :param tenant_id:
    :return:
    """
    context = dict(user=user.dict())
    tenant_data: Tenant = await tenant_controller.get_tenant_by_id(tenant_id=tenant_id)

    company_data: Company | None = None
    if tenant_data and tenant_data.company_id:
        company_data = await company_controller.get_company_internal(company_id=tenant_data.company_id)

    tenant_address: TenantAddress | None = None
    if tenant_data and tenant_data.address_id:
        tenant_address = await tenant_controller.get_tenant_address(address_id=tenant_data.address_id)

    tenant_payments = await lease_agreement_controller.load_tenant_payments(tenant_id=tenant_id)
    invoices: list[Invoice] = await lease_agreement_controller.get_invoices(tenant_id=tenant_id)
    historical_invoices = [invoice.dict() for invoice in invoices if invoice] if invoices else []
    paid_invoices = [invoice.dict() for invoice in invoices
                     if invoice.get_payment_status(payments=tenant_payments) == PaymentStatus.FULLY_PAID]
    un_paid_invoices = [invoice.dict() for invoice in invoices
                        if invoice.get_payment_status(payments=tenant_payments) != PaymentStatus.FULLY_PAID]

    unit = await lease_agreement_controller.get_leased_unit_by_tenant_id(tenant_id=tenant_id)
    unit_dicts = unit.dict() if isinstance(unit, Unit) else {}
    tenant_data_dict = tenant_data.dict() if isinstance(tenant_data, Tenant) else {}
    tenant_address_dict = tenant_address.dict() if isinstance(tenant_address, TenantAddress) else {}
    company_dict = company_data.dict() if isinstance(company_data, Company) else {}

    payment_dicts = [payment.dict() for payment in tenant_payments if payment] if tenant_payments else []
    statements_list = await lease_agreement_controller.load_tenant_statements(tenant_id=tenant_id)

    statements_dicts = [statement.dict() for statement in statements_list if statement] if statements_list else []

    context.update({'tenant': tenant_data_dict,
                    'address': tenant_address_dict,
                    'company': company_dict,
                    'paid_invoices': paid_invoices,
                    'unpaid_invoices': un_paid_invoices,
                    'historical_invoices': historical_invoices,
                    'unit': unit_dicts,
                    'payment_receipts': payment_dicts,
                    'statements': statements_dicts})

    return render_template("tenants/tenant_details.html", **context)


@tenants_route.post('/admin/tenant-address/<string:tenant_id>')
@login_required
async def create_tenant_address(user: User, tenant_id: str):
    """

    :param user:
    :param tenant_id:
    :return:
    """
    try:
        tenant_address = CreateTenantAddress(**request.form)
    except ValidationError as e:
        flash(message="Unable to create Tenant Address please fill in all required fields", category="danger")
        return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id), code=302)
    tenant_address_: TenantAddress = await tenant_controller.create_tenant_address(tenant_id=tenant_id,
                                                                                   tenant_address=tenant_address)
    tenant: Tenant = await tenant_controller.get_tenant_by_id(tenant_id=tenant_id)
    if tenant:
        tenant.address_id = tenant_address_.address_id
        updated_tenant = await tenant_controller.update_tenant(tenant=tenant)
        flash(message="Successfully updated tenant", category="success")
        return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id), code=302)
    flash(message="Unable to update Tenant Address", category="danger")
    return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id), code=302)


@tenants_route.post('/admin/tenant-email/<string:tenant_id>')
@login_required
async def do_send_email(user: User, tenant_id: str):
    """
        **send_email**
            will send email message to Tenant
    :param tenant_id:
    :param user:
    :return:
    """
    try:
        send_email_data = TenantSendMail(**request.form)
    except ValidationError as e:
        flash(message="Unable to send email please fill in all required fields", category="danger")
        return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id), code=302)

    if not (send_email_data.message and send_email_data.subject):
        flash(message="Unable to send email please fill in all required fields", category="danger")
        return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id), code=302)

    _ = await send_mail.send_mail_resend(email=EmailModel(to_=send_email_data.email, subject_=send_email_data.subject,
                                                          html_=send_email_data.message))

    flash(message="Email sent successfully", category="success")
    return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id), code=302)

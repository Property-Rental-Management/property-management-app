from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from pydantic import ValidationError

from src.emailer import EmailModel
from src.database.models.properties import Property
from src.database.models.companies import Company
from src.database.models.tenants import QuotationForm, Tenant, CreateTenant, TenantSendMail, TenantAddress, \
    CreateTenantAddress
from src.main import tenant_controller, company_controller, send_mail
from src.authentication import login_required
from src.database.models.users import User

tenants_route = Blueprint('tenants', __name__)


@tenants_route.get('/admin/tenants-list')
@login_required
async def get_tenants(user: User):
    user_data = user.dict()

    companies: list[Company] = await company_controller.get_user_companies(user_id=user.user_id)

    all_tenants = []
    for company in companies:
        if isinstance(company, Company):
            tenants_list = await tenant_controller.get_tenants_by_company_id(company_id=company.company_id)

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
    user_data = user.dict()
    context = dict(user=user_data)
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

    tenant_data_dict = tenant_data.dict() if isinstance(tenant_data, Tenant) else {}
    tenant_address_dict = tenant_address.dict() if isinstance(tenant_address, TenantAddress) else {}
    company_dict = company_data.dict() if isinstance(company_data, Company) else {}

    context.update({'tenant': tenant_data_dict,
                    'tenant_address': tenant_address_dict,
                    'company': company_dict})

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
    tenant_address_: TenantAddress = await tenant_controller.create_tenant_address(tenant_id=tenant_id, tenant_address=tenant_address)
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
        flash(message="unable to send email please fill in all required fields", category="danger")
        return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id))

    # TODO - add the ability to respond to the email within the email.
    _ = await send_mail.send_mail_resend(email=EmailModel(to_=send_email_data.email, subject_=send_email_data.subject,
                                                          html_=send_email_data.message))
    print(send_email_data)
    flash(message="Email sent successfully", category="success")
    return redirect(url_for('tenants.get_tenant', tenant_id=tenant_id), code=302)

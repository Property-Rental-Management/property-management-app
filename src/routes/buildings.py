import calendar
import functools
from datetime import date

from flask import Blueprint, render_template, flash, redirect, url_for, request
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.companies import Company
from src.database.models.invoices import (CreateInvoicedItem, BillableItem, CreateUnitCharge,
                                          PrintInvoiceForm, UnitEMailInvoiceForm, PaymentStatus)
from src.database.models.lease import LeaseAgreement, CreateLeaseAgreement
from src.database.models.notifications import NotificationsModel
from src.database.models.properties import Property, Unit, AddUnit, UpdateProperty, CreateProperty, UpdateUnit, \
    CreateUnitRental
from src.database.models.tenants import Tenant
from src.database.models.users import User
from src.emailer import EmailModel
from src.logger import init_logger
from src.main import company_controller, notifications_controller, tenant_controller, lease_agreement_controller, \
    invoice_man, send_mail

buildings_route = Blueprint('buildings', __name__)
buildings_logger = init_logger("Buildings-Router")


async def get_common_context(user: User, building_id: str, property_editor: bool = False):
    user_data = user.dict()
    building_property: Property = await company_controller.get_property(user=user, property_id=building_id)
    property_units: list[Unit] = await company_controller.get_property_units(user=user, property_id=building_id)
    notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)

    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []
    billable_items_: list[BillableItem] = await company_controller.get_billable_items(building_id=building_id)
    billable_dicts = [bill.dict() for bill in billable_items_ if bill and not bill.deleted] if billable_items_ else []

    context = dict(
        user=user_data,
        property=building_property.dict(),
        property_editor=property_editor,
        notifications_list=notifications_dicts,
        units=[unit.dict() for unit in property_units],
        billable_items=billable_dicts
    )
    return context


@buildings_route.get('/dashboard/buildings')
@login_required
async def get_buildings(user: User):
    user_data = user.dict()
    notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)

    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []

    context = dict(user=user_data, notifications_list=notifications_dicts)
    return render_template('building/buildings.html', **context)


@buildings_route.get('/dashboard/building/<string:building_id>')
@login_required
async def get_building(user: User, building_id: str):
    """
        returns a specific building by building id
    :param user:
    :param building_id:
    :return:
    """
    context = await get_common_context(user=user, building_id=building_id)
    return render_template('building/building.html', **context)


@buildings_route.get('/dashboard/add-building/<string:company_id>')
@login_required
async def add_building(user: User, company_id: str):
    user_data = user.dict()

    company: Company = await company_controller.get_company(company_id=company_id, user_id=user.user_id)
    notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)

    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []

    context = dict(user=user_data, company=company.dict(), notifications_list=notifications_dicts)

    return render_template('building/add_building.html', **context)


@buildings_route.post('/dashboard/add-building/<string:company_id>')
@login_required
async def do_add_building(user: User, company_id: str):
    company: Company = await company_controller.get_company(company_id=company_id, user_id=user.user_id)
    try:
        property_data: CreateProperty = CreateProperty(**request.form)
    except ValidationError as e:
        buildings_logger.error(f"Create building Error : {str(e)}")
        _message: str = "Unable to add Property"
        flash(message=_message, category="success")
        return redirect(url_for('companies.get_company', company_id=company.company_id), code=302)

    property_data.company_id = company.company_id
    property_model: Property = await company_controller.add_property(user=user, _property=property_data)

    if property_model is None:
        _message: str = "Unable to add Property"
        flash(message=_message, category="success")
        return redirect(url_for('companies.get_company', company_id=company.company_id), code=302)

    _message: str = f"Property : {property_model.name.title()} Successfully added to : {company.company_name.title()}"

    flash(message=_message, category="success")
    return redirect(url_for('companies.get_company', company_id=company.company_id), code=302)


@buildings_route.get('/dashboard/edit-building/<string:building_id>')
@login_required
async def edit_building(user: User, building_id: str):
    context = await get_common_context(user, building_id, property_editor=True)
    return render_template('building/building.html', **context)


@buildings_route.post('/dashboard/edit-building/<string:building_id>')
@login_required
async def do_edit_building(user: User, building_id: str):
    company_id: str = request.form.get('company_id')
    try:
        updated_building: UpdateProperty = UpdateProperty(**request.form)

    except ValidationError as e:
        buildings_logger.error(f"Error Updating Building : {str(e)}")
        flash(message="Error updating Property/Building...", category="danger")
        return redirect(url_for('companies.get_company', company_id=company_id), code=302)

    _property = await company_controller.update_property(user=user, property_details=updated_building)
    if _property is None:
        flash(message="Error updating Property/Building...", category="danger")
        return redirect(url_for('companies.get_company', company_id=company_id), code=302)

    context = await get_common_context(user=user, building_id=building_id)
    return render_template('building/building.html', **context)


@buildings_route.post('/dashboard/add-unit/<string:building_id>')
@login_required
async def do_add_unit(user: User, building_id: str):
    _ = user.dict()
    try:
        unit_data: AddUnit = AddUnit(**request.form)

        _ = await company_controller.add_unit(user=user, unit_data=unit_data, property_id=building_id)
        flash(message="Unit Added Successfully", category="success")
    except ValidationError as e:
        buildings_logger.error(f"error raised when adding Unit : {str(e)}")
        flash(message="To Add a Unit please Fill in all Fields", category="danger")

    return redirect(url_for('buildings.get_building', building_id=building_id), code=302)


# noinspection DuplicatedCode
@buildings_route.get('/dashboard/building/<string:building_id>/unit/<string:unit_id>')
@login_required
async def get_unit(user: User, building_id: str, unit_id: str):
    """
        **get_unit**
            obtains rental unit
    :param user:
    :param building_id:
    :param unit_id:
    :return:
    """
    context = dict(user=user.dict())
    historical_invoices = []
    paid_invoices = []
    un_paid_invoices = []
    unit_data: Unit = await company_controller.get_unit(user=user, building_id=building_id, unit_id=unit_id)

    if unit_data and unit_data.tenant_id:
        tenant_data: Tenant = await tenant_controller.get_tenant_by_id(tenant_id=unit_data.tenant_id)
        context.update({'tenant': tenant_data.dict()})
        tenant_payments = await lease_agreement_controller.load_tenant_payments(tenant_id=unit_data.tenant_id)
        invoices = await lease_agreement_controller.get_invoices(tenant_id=tenant_data.tenant_id)

        historical_invoices = [invoice.dict() for invoice in invoices if invoice] if invoices else []
        paid_invoices = [invoice.dict() for invoice in invoices
                         if invoice.get_payment_status(payments=tenant_payments) == PaymentStatus.FULLY_PAID]
        un_paid_invoices = [invoice.dict() for invoice in invoices
                            if invoice.get_payment_status(payments=tenant_payments) != PaymentStatus.FULLY_PAID]

        if tenant_data.company_id:
            company_data: Company = await company_controller.get_company_internal(company_id=tenant_data.company_id)
            if company_data:
                context.update({'company': company_data.dict()})
            bank_account = await company_controller.get_bank_account_internal(company_id=company_data.company_id)
            if bank_account:
                context.update({'bank_account': bank_account.dict()})

    else:
        tenants_list: list[Tenant] = await tenant_controller.get_un_booked_tenants()
        context.update({'tenants': tenants_list})

    billable_items_: list[BillableItem] = await company_controller.get_billable_items(building_id=building_id)
    billable_dicts: list[dict[str, str | int]] = [item.dict()
                                                  for item in billable_items_ if item] if billable_items else []

    charged_items_dicts = await build_charge_items(building_id=building_id, unit_id=unit_id)

    if unit_data is None:
        flash(message="Could not find Unit with that ID", category="danger")
        redirect(url_for('buildings.get_building', building_id=building_id))

    month_options = await get_month_options()

    context.update({'unit': unit_data,
                    'billable_items': billable_dicts,
                    'charged_items': charged_items_dicts,
                    'paid_invoices': paid_invoices,
                    'unpaid_invoices': un_paid_invoices,
                    'historical_invoices': historical_invoices,
                    'month_options': month_options})

    return render_template('building/units/unit.html', **context)


async def get_month_options():
    # Get a list of month names
    month_names = list(calendar.month_name)[1:]
    # Generate the month options data
    month_options = [(month_number, month_name) for month_number, month_name in enumerate(month_names, start=1)]
    return month_options


async def build_charge_items(building_id, unit_id):
    charged_items = await company_controller.get_charged_items(building_id=building_id, unit_id=unit_id)

    charged_items_dicts = [item.dict() for item in charged_items if item] if charged_items else []
    response_data = []
    for item in charged_items_dicts:
        _data = item
        billable_item: BillableItem = await company_controller.get_item_by_number(item_number=item.get('item_number'))
        _data["item"] = billable_item.dict()
        response_data.append(_data)

    return response_data


@buildings_route.post('/dashboard/building/<string:building_id>/unit/<string:unit_id>')
@login_required
async def add_tenant_to_building_unit(user: User, building_id: str, unit_id: str):
    """
        add_tenant_to_building_unit
    :param user:
    :param building_id:
    :param unit_id:
    :return:
    """

    context = dict(user=user.dict())
    tenant_rental: CreateUnitRental = CreateUnitRental(**request.form)
    _updated_unit = await company_controller.update_unit(user_id=user.user_id, unit_data=tenant_rental)

    if _updated_unit:
        context.update(dict(unit=_updated_unit.dict()))

    building_ = await company_controller.get_property_by_id_internal(property_id=tenant_rental.property_id)
    if not building_:
        message: str = "Unable to locate the building which should be rented"
        flash(message=message, category="danger")
        return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id))

    tenant: Tenant = await tenant_controller.get_tenant_by_id(tenant_id=tenant_rental.tenant_id)

    args = dict(tenant=tenant, company_id=building_.company_id, start_date=tenant_rental.lease_start_date,
                end_date=tenant_rental.lease_end_date)

    tenant_: Tenant = await update_tenant_rental(**args)

    updated_tenant: Tenant = await tenant_controller.update_tenant(tenant=tenant_)

    if updated_tenant:
        context.update(dict(tenant=updated_tenant.dict()))

    deposit_amount = await lease_agreement_controller.calculate_deposit_amount(
        rental_amount=tenant_rental.rental_amount)

    rental_period: int = await convert_rental_period_to_days(rental_period=tenant_rental.rental_period,
                                                             other=tenant_rental.number_days)

    lease_dict = await create_lease_dict(deposit_amount=deposit_amount, rental_period=rental_period,
                                         tenant_rental=tenant_rental)

    try:
        lease_: CreateLeaseAgreement = CreateLeaseAgreement(**lease_dict)
        lease: LeaseAgreement = await lease_agreement_controller.create_lease_agreement(lease=lease_)
    except ValidationError as e:
        message: str = f"Error creating Lease Agreement : {str(e)}"
        buildings_logger.error(message)
        flash(message=message, category="danger")
        return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id))

    if lease:
        context.update(dict(lease_agreement=lease.dict()))

    building_.available_units -= 1
    updated_building: Property = await company_controller.update_property(user=user, property_details=building_)

    if updated_building:
        context.update(dict(building=updated_building.dict()))

    flash(message='Lease Agreement created Successfully', category="success")
    return render_template('tenants/official/tenant_rental_result.html', **context)


async def create_lease_dict(deposit_amount: int, rental_period: int, tenant_rental: CreateUnitRental):
    """
        **create_lease_dict**
    :param deposit_amount:
    :param rental_period:
    :param tenant_rental:
    :return:
    """
    return dict(property_id=tenant_rental.property_id,
                tenant_id=tenant_rental.tenant_id,
                unit_id=tenant_rental.unit_id,
                start_date=tenant_rental.lease_start_date,
                end_date=tenant_rental.lease_end_date,
                rent_amount=tenant_rental.rental_amount,
                deposit_amount=deposit_amount,
                payment_period=rental_period,
                is_active=True)


async def update_tenant_rental(tenant: Tenant, company_id: str, start_date: date, end_date: date) -> Tenant:
    """

    :param tenant:
    :param company_id:
    :param start_date:
    :param end_date:
    :return:
    """
    tenant.is_renting = True
    tenant.lease_start_date = start_date
    tenant.lease_end_date = end_date
    tenant.company_id = company_id
    return tenant


@buildings_route.post('/dashboard/update-tenant-unit/<string:building_id>/unit/<string:unit_id>')
@login_required
async def update_tenant_to_building_unit(user: User, building_id: str, unit_id: str):
    """
    **update_tenant_to_building_unit**

    :param unit_id:
    :param building_id:
    :param user:
    :return:
    """
    try:
        tenant_data: Tenant | None = Tenant(**request.form)
    except ValidationError as e:
        buildings_logger.error(str(e))
        flash(message="Unable to update tenant data", category="danger")
        return redirect(url_for("buildings.get_unit", building_id=building_id, unit_id=unit_id), code=302)

    if not tenant_data:
        flash(message="Unable to update tenant data", category="danger")
        return redirect(url_for("buildings.get_unit", building_id=building_id, unit_id=unit_id), code=302)

    _ = await tenant_controller.update_tenant(tenant=tenant_data)

    flash(message="Tenant Data updated", category="success")
    return redirect(url_for("buildings.get_unit", building_id=building_id, unit_id=unit_id), code=302)


@buildings_route.post('/dashboard/building/billable')
@login_required
async def billable_items(user: User):
    """
    **billable_items**

    :param user:
    :return:
    """
    billable_item: CreateInvoicedItem = CreateInvoicedItem(**request.form)
    billable_item: CreateInvoicedItem = await company_controller.create_billable_item(billable_item=billable_item)
    flash(message="Billable Item Added to building", category="success")
    return redirect(url_for("buildings.get_building", building_id=billable_item.property_id), code=302)


@buildings_route.post('/dashboard/building/billed-item/<string:property_id>/<string:item_number>')
@login_required
async def get_billed_item(user: User, property_id: str, item_number: str):
    """
    **get_billed_item**

    :param user:
    :param property_id:
    :param item_number:
    :return:
    """
    billed_item: CreateInvoicedItem = company_controller.get_billed_item(property_id=property_id,
                                                                         item_number=item_number)
    return billed_item


@buildings_route.get('/dashboard/building/delete-billed-item/<string:property_id>/<string:item_number>')
@login_required
async def delete_billed_item(user: User, property_id: str, item_number: str):
    """
    **delete_billed_item**

    :param user:
    :param property_id:
    :param item_number:
    :return:
    """
    billed_item: CreateInvoicedItem = await company_controller.delete_billed_item(property_id=property_id,
                                                                                  item_number=item_number)
    flash(message=f"Billable Item : {billed_item.description} Deleted", category="success")
    return redirect(url_for("buildings.get_building", building_id=property_id), code=302)


@buildings_route.post('/dashboard/building/create-charge')
@login_required
async def create_billing_charge(user: User):
    """
    **create_billing_charge**

    :param user:
    :return:

    """
    try:
        unit_charge_item: CreateUnitCharge = CreateUnitCharge(**request.form)
    except ValidationError:
        flash(message="Please indicate all required fields in order to create a charge", category="danger")
        _redirect_link = dict(building_id=request.form.get('property_id'))
        return redirect(url_for("buildings.get_building", **_redirect_link), code=302)
    if not (unit_charge_item.item_number and unit_charge_item.amount):
        flash(message="Please indicate all required fields in order to create a charge", category="danger")
        _redirect_link = dict(building_id=request.form.get('property_id'))
        return redirect(url_for("buildings.get_building", **_redirect_link), code=302)

    _ = await company_controller.create_unit_bill_charge(charge_item=unit_charge_item)
    flash(message="Billing Charge Added to Unit", category="success")
    return redirect(url_for("buildings.get_unit", building_id=unit_charge_item.property_id,
                            unit_id=unit_charge_item.unit_id), code=302)


@buildings_route.get('/dashboard/building/delete-charge/<string:charge_id>')
@login_required
async def delete_charge(user: User, charge_id: str):
    """

    :param user:
    :param charge_id:
    :return:
    """
    deleted_charge_item: CreateUnitCharge = await company_controller.delete_unit_charge(charge_id=charge_id)
    # get_unit
    flash(message="Charge Successfully Deleted", category="success")
    return redirect(url_for("buildings.get_unit", building_id=deleted_charge_item.property_id,
                            unit_id=deleted_charge_item.unit_id), code=302)


@buildings_route.post('/dashboard/building/update-unit/<string:unit_id>')
@login_required
async def updated_unit(user: User, unit_id: str):
    """
    **updated_unit**

    :param unit_id:
    :param user:
    :return:
    """
    update_unit_model: UpdateUnit = UpdateUnit(**request.form)
    _updated_unit: Unit | None = None
    if unit_id == update_unit_model.unit_id:
        _updated_unit = await company_controller.update_unit(user_id=user.user_id, unit_data=update_unit_model)
    else:
        _updated_unit = None

    if _updated_unit:
        flash(message="Successfully Updated Unit", category="success")
    else:
        flash(message="Unable to Update Unit", category="danger")

    return redirect(url_for("buildings.get_unit", building_id=update_unit_model.property_id,
                            unit_id=update_unit_model.unit_id), code=302)


@buildings_route.post('/dashboard/unit-print-invoice')
@login_required
async def unit_print_invoice(user: User):
    """
    **unit_print_invoice**

    :param user:
    :return:
    """
    try:
        print_invoice_form = PrintInvoiceForm(**request.form)
    except ValidationError as e:
        building_id = request.form.get('building_id')
        unit_id = request.form.get('unit_id')

        _vars = dict(building_id=building_id, unit_id=unit_id)
        flash(message="Please indicate what you want to print", category="danger")
        return redirect(url_for("buildings.get_unit", **_vars))

    invoice_to_print = await lease_agreement_controller.get_invoice(invoice_number=print_invoice_form.invoice_number)
    if invoice_to_print is None:
        flash(message="Invoice not found", category="danger")
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))

    context = {'invoice': invoice_to_print.dict()}
    building: Property = await company_controller.get_property(user=user, property_id=print_invoice_form.building_id)
    if building is None:
        flash(message="Property not found", category="danger")
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))
    buildings_logger.info(f"Company Data : {building.company_id}")
    company: Company = await company_controller.get_company_internal(company_id=building.company_id)
    bank_account = await company_controller.get_bank_account_internal(company_id=building.company_id)
    buildings_logger.info(f"Bank Account : {bank_account}")

    if company is None:
        flash(message="Company not found", category="danger")
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))
    if bank_account is None:
        flash(message="Bank Account not found - please add bank account details before printing invoices",
              category="danger")
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))

    context['company'] = company.dict()
    context['bank_account'] = bank_account.dict()
    return render_template('reports/invoice_report.html', **context)


@buildings_route.post('/dashboard/email-invoices')
@login_required
async def do_send_invoice_email(user: User):
    """
        **do_send_invoice_email*8
    :param user:
    :return:
    """
    invoice_email_form: UnitEMailInvoiceForm | None = None
    try:
        invoice_email_form = await process_send_mail_form()
    except ValidationError as e:
        buildings_logger.error(str(e))
        return redirect(url_for('buildings.get_unit', building_id=invoice_email_form.building_id,
                                unit_id=invoice_email_form.unit_id), code=302)

    invoice_link_func = functools.partial(invoice_man.create_invoice_link, building_id=invoice_email_form.building_id)
    url_list = [await invoice_link_func(invoice_number=invoice_number)
                for invoice_number in invoice_email_form.invoice_numbers]

    message: str = invoice_email_form.message
    to_: str = invoice_email_form.email
    subject_: str = invoice_email_form.subject

    message_ = await format_email_message(message, url_list)
    new_mail = dict(to_=to_, subject_=subject_, html_=message_)
    await send_mail.send_mail_resend(email=EmailModel(**new_mail))

    flash(message="Email Sent with selected invoices", category="success")
    return redirect(url_for('buildings.get_unit', building_id=invoice_email_form.building_id,
                            unit_id=invoice_email_form.unit_id), code=302)


async def format_email_message(message: str, url_list: list[str]):
    """
        **format_email_message**
            formatting email message
    :param message:
    :param url_list:
    :return:
    """
    links = "\n".join(f"<li class='list-group-item'><a href='{url}'>{url}</a></li>" for url in url_list)
    formatted_links = f"<ul class='list-group'>{links}</ul>"
    message_ = f"""
    {message}

    <h3>Invoices are attached below:</h3>

    {formatted_links}
    """
    return message_


async def process_send_mail_form() -> UnitEMailInvoiceForm:
    invoice_numbers = request.form.getlist('invoice_numbers[]')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    building_id = request.form.get('building_id')
    unit_id = request.form.get('unit_id')
    invoice_email_dict = dict(invoice_numbers=invoice_numbers, email=email, subject=subject,
                              message=message, building_id=building_id, unit_id=unit_id)
    return UnitEMailInvoiceForm(**invoice_email_dict)


async def convert_rental_period_to_days(rental_period: str, other: str) -> int:
    _other = int(other) if other.isdecimal() else 0
    rental_periods = {"daily": 1, "weekly": 7, "monthly": 30}
    return rental_periods.get(rental_period, _other)

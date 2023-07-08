from flask import Blueprint, render_template, flash, redirect, url_for, request
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.companies import Company
from src.database.models.invoices import CreateInvoicedItem, BillableItem, CreateUnitCharge, PrintInvoiceForm
from src.database.models.lease import LeaseAgreement, CreateLeaseAgreement
from src.database.models.notifications import NotificationsModel
from src.database.models.properties import Property, Unit, AddUnit, UpdateProperty, CreateProperty, UpdateUnit
from src.database.models.tenants import Tenant
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller, notifications_controller, tenant_controller, lease_agreement_controller

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


@buildings_route.get('/admin/buildings')
@login_required
async def get_buildings(user: User):
    user_data = user.dict()
    notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)

    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []

    context = dict(user=user_data, notifications_list=notifications_dicts)
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
    context = await get_common_context(user=user, building_id=building_id)
    return render_template('building/building.html', **context)


@buildings_route.get('/admin/add-building/<string:company_id>')
@login_required
async def add_building(user: User, company_id: str):
    user_data = user.dict()

    company: Company = await company_controller.get_company(company_id=company_id, user_id=user.user_id)
    notifications: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)

    notifications_dicts = [notice.dict() for notice in notifications.unread_notification] if notifications else []

    context = dict(user=user_data, company=company.dict(), notifications_list=notifications_dicts)

    return render_template('building/add_building.html', **context)


@buildings_route.post('/admin/add-building/<string:company_id>')
@login_required
async def do_add_building(user: User, company_id: str):
    company: Company = await company_controller.get_company(company_id=company_id, user_id=user.user_id)
    property_data: CreateProperty = CreateProperty(**request.form)
    property_data.company_id = company.company_id
    property_model: Property = await company_controller.add_property(user=user, _property=property_data)

    _message: str = f"Property : {property_model.name.title()} Successfully added to : {company.company_name.title()}"

    flash(message=_message, category="success")
    return redirect(url_for('companies.get_company', company_id=company.company_id), code=302)


@buildings_route.get('/admin/edit-building/<string:building_id>')
@login_required
async def edit_building(user: User, building_id: str):
    context = await get_common_context(user, building_id, property_editor=True)
    return render_template('building/building.html', **context)


@buildings_route.post('/admin/edit-building/<string:building_id>')
@login_required
async def do_edit_building(user: User, building_id: str):
    try:
        updated_building: UpdateProperty = UpdateProperty(**request.form)
        _property = await company_controller.update_property(user=user, property_details=updated_building)
        if _property is not None:
            flash(message="Successfully updated Property/Building", category="success")
    except ValidationError as e:
        print(f"error {str(e)}")
        flash(message="Error updating Property/Building...", category="danger")

    context = await get_common_context(user=user, building_id=building_id)
    return render_template('building/building.html', **context)


@buildings_route.post('/admin/add-unit/<string:building_id>')
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


@buildings_route.get('/admin/building/<string:building_id>/unit/<string:unit_id>')
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
    historical_invoices = {}
    unit_data: Unit = await company_controller.get_unit(user=user, building_id=building_id, unit_id=unit_id)

    if unit_data and unit_data.tenant_id:
        tenant_data: Tenant = await tenant_controller.get_tenant_by_id(tenant_id=unit_data.tenant_id)
        context.update({'tenant': tenant_data.dict()})
        historical_invoices = await lease_agreement_controller.get_invoices(tenant_id=tenant_data.tenant_id)

        if tenant_data.company_id:
            company_data: Company = await company_controller.get_company_internal(company_id=tenant_data.company_id)
            if company_data:
                context.update({'company': company_data.dict()})

    else:
        tenants_list: list[Tenant] = await tenant_controller.get_un_booked_tenants()
        context.update({'tenants': tenants_list})

    billable_items_: list[BillableItem] = await company_controller.get_billable_items(building_id=building_id)
    billable_dicts: list[dict[str, str | int]] = [item.dict()
                                                  for item in billable_items_ if item] if billable_items else []

    charged_items_dicts = await build_charge_items(building_id, unit_id)

    if unit_data is None:
        flash(message="Could not find Unit with that ID", category="danger")
        redirect(url_for('buildings.get_building', building_id=building_id))

    context.update({'unit': unit_data,
                    'billable_items': billable_dicts,
                    'charged_items': charged_items_dicts,
                    'historical_invoices': historical_invoices})

    return render_template('building/units/unit.html', **context)


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


@buildings_route.post('/admin/building/<string:building_id>/unit/<string:unit_id>')
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
    tenant_rental = Unit(**request.form)
    _updated_unit = await company_controller.update_unit(user_id=user.user_id, unit_data=tenant_rental)

    if _updated_unit:
        context.update(dict(unit=_updated_unit.dict()))

    tenant: Tenant = await tenant_controller.get_tenant_by_id(tenant_id=tenant_rental.tenant_id)
    tenant.is_renting = True
    tenant.lease_start_date = tenant_rental.lease_start_date
    tenant.lease_end_date = tenant_rental.lease_end_date
    updated_tenant = await tenant_controller.update_tenant(tenant=tenant)

    if updated_tenant:
        context.update(dict(tenant=updated_tenant.dict()))

    deposit_amount = await lease_agreement_controller.calculate_deposit_amount(
        rental_amount=tenant_rental.rental_amount)

    lease_dict: dict[str, str] = dict(property_id=tenant_rental.property_id,
                                      tenant_id=tenant_rental.tenant_id,
                                      unit_id=tenant_rental.unit_id,
                                      start_date=tenant_rental.lease_start_date,
                                      end_date=tenant_rental.lease_end_date,
                                      rent_amount=tenant_rental.rental_amount,
                                      deposit_amount=deposit_amount,
                                      is_active=True)

    try:
        lease_: CreateLeaseAgreement = CreateLeaseAgreement(**lease_dict)
        lease: LeaseAgreement = await lease_agreement_controller.create_lease_agreement(lease=lease_)
    except ValidationError as e:
        buildings_logger.error(f"Error creating Lease Agreement : {str(e)}")
        flash(message=f"Validation error : {str(e)}", category="danger")
        return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id))
    if lease:
        context.update(dict())
    building_: Property = await company_controller.get_property_by_id_internal(property_id=building_id)
    building_.available_units -= 1
    updated_building: Property = await company_controller.update_property(user=user, property_details=building_)
    print(f'Updated Building : {updated_building}')
    if updated_building:
        context.update(dict(building=updated_building.dict()))

    flash(message='Lease Agreement created Successfully', category="success")
    return render_template('tenants/official/tenant_rental_result.html', **context)


@buildings_route.post('/admin/update-tenant-unit/<string:building_id>/unit/<string:unit_id>')
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


@buildings_route.post('/admin/building/billable')
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


@buildings_route.post('/admin/building/billed-item/<string:property_id>/<string:item_number>')
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


@buildings_route.get('/admin/building/delete-billed-item/<string:property_id>/<string:item_number>')
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


@buildings_route.post('/admin/building/create-charge')
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
    return redirect(url_for("buildings.get_building", building_id=unit_charge_item.property_id), code=302)


@buildings_route.get('/admin/building/delete-charge/<string:charge_id>')
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


@buildings_route.post('/admin/building/update-unit/<string:unit_id>')
@login_required
async def updated_unit(user: User, unit_id: str):
    """
    **updated_unit**

    :param unit_id:
    :param user:
    :return:
    """
    update_unit_model: UpdateUnit = UpdateUnit(**request.form)
    if unit_id == update_unit_model.unit_id:
        _updated_unit: Unit = await company_controller.update_unit(user_id=user.user_id, unit_data=update_unit_model)
    else:
        _updated_unit = None

    if _updated_unit:
        flash(message="Successfully Updated Unit", category="success")
    else:
        flash(message="Unable to Update Unit", category="danger")

    return redirect(url_for("buildings.get_unit",
                            building_id=update_unit_model.property_id,
                            unit_id=update_unit_model.unit_id), code=302)


@buildings_route.post('/admin/unit-print-invoice')
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
        print(dict(**request.form))
        _vars = dict(building_id=building_id, unit_id=unit_id)
        flash(message="Please indicate what you want to print", category="danger")
        return redirect(url_for("buildings.get_unit", **_vars))

    invoice_to_print = await lease_agreement_controller.get_invoice(invoice_number=print_invoice_form.invoice_number)
    if invoice_to_print is None:
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))

    context = {'invoice': invoice_to_print.dict()}
    building: Property = await company_controller.get_property(user=user, property_id=print_invoice_form.building_id)
    if building is None:
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))

    company: Company = await company_controller.get_company(user=user, company_id=building.company_id)
    bank_account = await company_controller.get_bank_accounts(user=user, company_id=building.company_id)

    if company is None:
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))
    if bank_account is None:
        return redirect(url_for('buildings.get_unit', building_id=print_invoice_form.building_id,
                                unit_id=print_invoice_form.unit_id))

    context['company'] = company.dict()
    context['bank_account'] = bank_account.dict()
    return render_template('reports/invoice_report.html', **context)

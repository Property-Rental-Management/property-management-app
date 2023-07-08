from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.companies import Company
from src.database.models.invoices import UnitCreateInvoiceForm, UnitCharge, Invoice
from src.database.models.properties import Property
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller, lease_agreement_controller

invoices_route = Blueprint('invoices', __name__)
invoice_logger = init_logger('invoice_logger')


@invoices_route.get('/admin/invoices')
@login_required
async def get_invoices(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('invoices/invoices.html', **context)


@invoices_route.post('/admin/invoice/create-invoice')
@login_required
async def create_invoice(user: User):
    """

    :param user:
    :return:
    """
    try:
        invoice_data: UnitCreateInvoiceForm = UnitCreateInvoiceForm(**request.form)
        invoice_logger.info(invoice_data.dict())
    except ValidationError as e:
        invoice_logger.error(str(e))
        invoice_logger.error(dict(**request.form))
        message_dict = dict(message="Unable to create invoice please input all required fields", category="danger")
        return await redirect_to_unit(message_dict)

    if not (invoice_data.charge_ids or invoice_data.rental_amount):
        invoice_logger.error("bad values either on charge_ids or rental_amount")
        message_dict = dict(message="please indicate what to invoice", category="danger")
        return await redirect_to_unit(message_dict)

    _vars = dict(building_id=invoice_data.property_id, unit_id=invoice_data.unit_id)
    unit_charges: list[UnitCharge] = await company_controller.get_charged_items(**_vars)
    if unit_charges:
        invoice_logger.info(f"found unit charges : {unit_charges}")
    invoice_charges: list[UnitCharge] = [charge for charge in unit_charges if
                                         charge.charge_id in invoice_data.charge_ids] if invoice_data.charge_ids else []

    unit_ = await company_controller.get_unit(user=user, building_id=invoice_data.property_id,
                                              unit_id=invoice_data.unit_id)
    if not unit_:
        invoice_logger.info(f"Unit not found")
        message_dict = dict(message="Invoiced Unit not Found", category="danger")
        return await redirect_to_unit(message_dict)

        # checking if rental amount should be included - remember rental_amount is a checkbox -
        # the actual rental amount is on unit_

    include_rental: bool = invoice_data.rental_amount == "on"
    due_after = invoice_data.due_after
    created_invoice: Invoice = await lease_agreement_controller.create_invoice(invoice_charges=invoice_charges,
                                                                               unit_=unit_,
                                                                               include_rental=include_rental,
                                                                               due_after=due_after)
    if not created_invoice:
        message_dict = dict(message="Unable to create invoice", category="danger")
        return await redirect_to_unit(message_dict)

    property_: Property = await company_controller.get_property_by_id_internal(property_id=invoice_data.property_id)
    if not property_:
        message_dict = dict(message="Invoiced Property not found", category="danger")
        return await redirect_to_unit(message_dict)

    company_data: Company = await company_controller.get_company_internal(company_id=property_.company_id)
    if not company_data:
        message_dict = dict(message="Invoiced Property not found", category="danger")
        return await redirect_to_unit(message_dict)

    _title = f"{property_.name} - Invoice"
    flash(message="Successfully created Invoice", category="success")
    bank_account = await company_controller.get_bank_account_internal(company_id=company_data.company_id)

    if not bank_account:
        message_dict = dict(message="Company Bank Account not found", category="danger")
        return await redirect_to_unit(message_dict)

    bank_account_dict = bank_account.dict()

    context = dict(invoice=created_invoice.dict(), company=company_data.dict(), title=_title,
                   bank_account=bank_account_dict)

    return render_template('reports/invoice_report.html', **context)


async def redirect_to_unit(message_dict: dict[str, str]):
    _vars = dict(building_id=request.form.get('property_id'), unit_id=request.form.get('unit_id'))
    print(vars)
    flash(**message_dict)
    return redirect(url_for('buildings.get_unit', **_vars), code=302)

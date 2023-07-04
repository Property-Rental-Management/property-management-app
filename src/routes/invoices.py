from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from database.models.properties import Unit
from src.main import company_controller, lease_agreement_controller
from src.database.models.invoices import UnitCreateInvoiceForm, UnitCharge, Invoice
from src.authentication import login_required
from src.database.models.users import User

invoices_route = Blueprint('invoices', __name__)


@invoices_route.get('/admin/invoices')
@login_required
async def get_invoices(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('invoices/invoices.html', **context)


@invoices_route.post('/admin/invoice/create-invoice')
@login_required
async def create_invoice(user: User) -> Invoice:
    """

    :param user:
    :return:
    """
    try:
        invoice_data: UnitCreateInvoiceForm = UnitCreateInvoiceForm(**request.form)
    except ValidationError as e:
        message_dict = dict(message="Unable to create invoice please input all required fields",
                            category="danger")
        return await redirect_to_unit(message_dict)

    if not (invoice_data.charge_ids or invoice_data.rental_amount):
        message_dict = dict(message="please indicate what to invoice",
                            category="danger")
        return await redirect_to_unit(message_dict)
    _vars = dict(building_id=invoice_data.property_id, unit_id=invoice_data.unit_id)
    unit_charges: list[UnitCharge] = await company_controller.get_charged_items(**_vars)
    invoice_charges: list[UnitCharge] = [charge for charge in unit_charges if
                                         charge.charge_id in invoice_data.charge_ids] if invoice_data.charge_ids else []
    unit_: Unit | None = None
    if invoice_data.rental_amount:
        unit_ = await company_controller.get_unit(user=user, building_id=invoice_data.property_id,
                                                  unit_id=invoice_data.unit_id)
    else:
        unit_ = None
    created_invoice: Invoice = await lease_agreement_controller.create_invoice(invoice_charges, unit_)


async def redirect_to_unit(message_dict: dict[str, str]):
    _vars = dict(building_id=request.form.get('property_id'), unit_id=request.form.get('unit_id'))
    flash(**message_dict)
    return redirect(url_for('buildings.get_unit', **_vars), code=302)

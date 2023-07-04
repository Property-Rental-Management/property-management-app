from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.database.models.invoices import UnitCreateInvoiceForm
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
async def create_invoice(user: User):
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

    if not (invoice_data.charge_ids and invoice_data.rental_amount):
        message_dict = dict(message="please indicate what to invoice",
                            category="danger")
        return await redirect_to_unit()


async def redirect_to_unit(message_dict: dict[str, str]):
    _vars = dict(building_id=request.form.get('property_id'), unit_id=request.form.get('unit_id'))
    flash(**message_dict)
    return redirect(url_for('buildings.get_unit', **_vars), code=302)

from flask import Blueprint, render_template, request, url_for, redirect, flash
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.invoices import Invoice
from src.database.models.payments import UnitInvoicePaymentForm, CreatePayment
from src.database.models.users import User
from src.logger import init_logger
from src.main import lease_agreement_controller

payments_route = Blueprint('payments', __name__)
payment_logger = init_logger("PAYMENT Router")


@payments_route.get('/admin/payments')
@login_required
async def get_payments(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('payments/payments.html', **context)


@payments_route.post('/admin/get-unit-payment/<int:invoice_number>')
@login_required
async def create_unit_payment(user: User, invoice_number: int):
    """
    **get_unit_payment**
        will return payment form for use in unit payments
    :param invoice_number:
    :param user:
    :return:
    """
    try:
        invoice_payment_form = UnitInvoicePaymentForm(**request.form)
    except ValidationError as e:
        payment_logger.error(str(e))
        flash(message="validation error, please input all required fields", category="danger")
        building_id = request.form.get('property_id')
        unit_id = request.form.get('unit_id')
        return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id), code=302)

    if invoice_payment_form.invoice_number != invoice_number:
        flash(message="Bad Request", category="danger")
        return redirect(url_for('home.get_home'), code=302)

    payment_logger.info(invoice_payment_form)

    invoice: Invoice = await lease_agreement_controller.get_invoice(invoice_number=invoice_number)
    new_payment_dict = dict(
        invoice_number=invoice_number,
        tenant_id=invoice_payment_form.tenant_id,
        property_id=invoice_payment_form.property_id,
        unit_id=invoice_payment_form.unit_id,
        amount_paid=invoice_payment_form.amount_paid)
    payment_instance = CreatePayment(**new_payment_dict)
    context = {'user': user.dict(),
               'invoice': invoice.dict(),
               'payment': payment_instance.dict()}

    return render_template('payments/verify_payment.html', **context)


@payments_route.get('/admin/verify-payments')
@login_required
async def do_verify_payment(user: User):
    """

    :param user:
    :return:
    """
    pass

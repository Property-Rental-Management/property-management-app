from datetime import date

from flask import Blueprint, render_template, request, url_for, redirect, flash
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.invoices import Invoice
from src.database.models.payments import UnitInvoicePaymentForm, CreatePayment, PaymentVerificationForm, Payment, \
    UpdatePayment
from src.database.models.users import User
from src.logger import init_logger
from src.main import lease_agreement_controller, company_controller

payments_route = Blueprint('payments', __name__)
payment_logger = init_logger("PAYMENT Router")


async def get_payment_context(user: User, payment_instance: Payment) -> dict[str, dict[str, int | str | date]]:
    invoice: Invoice = await lease_agreement_controller.get_invoice(invoice_number=payment_instance.invoice_number)
    building = await company_controller.get_property_by_id_internal(payment_instance.property_id)
    company = await company_controller.get_company_internal(company_id=building.company_id)

    return {'user': user.dict(),
            'invoice': invoice.dict(),
            'payment': payment_instance.dict(),
            'company': company.dict()}


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
        amount_paid=invoice_payment_form.amount_paid,
        month=invoice.month)
    payment_instance: CreatePayment = CreatePayment(**new_payment_dict)

    context = {'user': user.dict(),
               'invoice': invoice.dict(),
               'payment': payment_instance.dict()}

    return render_template('payments/verify_payment.html', **context)


@payments_route.post('/admin/payments/verification')
@login_required
async def do_verify_payment(user: User):
    building_id = request.form.get('property_id')
    unit_id = request.form.get('unit_id')
    try:
        payment_verification = PaymentVerificationForm(**request.form)
    except ValidationError as e:
        message: str = f"Error in form : {str(e)}"
        payment_logger.error(message)
        flash(message=message, category="danger")
        return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id), code=302)

    payment_logger.info(f"Payment Verification: {payment_verification}")
    payment_instance = await lease_agreement_controller.add_payment(Payment(**payment_verification.dict()))
    if not payment_verification.is_successful:
        building_id = payment_verification.property_id
        unit_id = payment_verification.unit_id

        flash(message="Payment Not Verified", category="danger")
        return redirect(url_for('buildings.get_unit', building_id=building_id, unit_id=unit_id), code=302)

    context = await get_payment_context(user, payment_instance)

    return render_template("payments/payment_receipt.html", **context)


@payments_route.post('/admin/payments/print-receipt')
@login_required
async def print_payment_receipt(user: User):
    transaction_id = request.form.get('transaction_id')
    tenant_id = request.form.get('tenant_id')
    if not tenant_id or not transaction_id:
        flash(message="Error accessing tenant details", category="danger")
        return redirect(url_for('home.get_home'), code=302)

    payment_instance: Payment = await lease_agreement_controller.load_payment(transaction_id=transaction_id)
    if not (payment_instance and payment_instance.tenant_id == tenant_id):
        flash(message="Error accessing tenant details", category="danger")
        return redirect(url_for('home.get_home'), code=302)

    context = await get_payment_context(user, payment_instance)

    return render_template("payments/payment_receipt.html", **context)


@payments_route.get('/admin/edit-payment/<string:transaction_id>')
@login_required
async def edit_payment(user: User, transaction_id: str):
    """

    :param user:
    :param payment_id:
    :return:
    """
    payment_instance = await lease_agreement_controller.load_payment(transaction_id=transaction_id)
    if not payment_instance:
        flash(message="Error accessing tenant details", category="danger")
        return redirect(url_for('home.get_home'), code=302)

    context = await get_payment_context(user, payment_instance)

    return render_template("payments/edit_payment.html", **context)


@payments_route.post('/admin/edit-payment/<string:transaction_id>')
@login_required
async def do_update_payment(user: User, transaction_id: str):
    """
        **do_update_payment**
            will update payment record and then load payment receipt
    :param user:
    :param transaction_id:
    :return:
    """
    try:
        updated_payment: UpdatePayment = UpdatePayment(**request.form)
        payment_logger.info(f"Updated Payment: {updated_payment}")
    except ValidationError as e:
        payment_logger.error(str(e))
        flash(message="Error accessing tenant details", category="danger")
        return redirect(url_for('home.get_home'), code=302)

    payment_instance = await lease_agreement_controller.update_payment(payment_instance=updated_payment)

    context = await get_payment_context(user=user, payment_instance=payment_instance)

    return render_template("payments/payment_receipt.html", **context)

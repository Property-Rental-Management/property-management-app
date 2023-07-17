from flask import Blueprint, render_template, request, redirect, url_for, flash
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.companies import Company
from src.database.models.invoices import UnitCreateInvoiceForm, UnitCharge, Invoice, UnitPaymentForm, InvoiceUpdateModel
from src.database.models.properties import Property
from src.database.models.users import User
from src.logger import init_logger
from src.main import company_controller, lease_agreement_controller, invoice_man

invoices_route = Blueprint('invoices', __name__)
invoice_logger = init_logger('invoice_logger')


async def redirect_to_unit(message_dict: dict[str, str]):
    _vars = dict(building_id=request.form.get('property_id'), unit_id=request.form.get('unit_id'))
    print(vars)
    flash(**message_dict)
    return redirect(url_for('buildings.get_unit', **_vars), code=302)


@invoices_route.get('/admin/invoices')
@login_required
async def get_invoices(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('invoices/invoices.html', **context)


@invoices_route.get('/reports/invoice/<string:building_id>/<string:invoice_number>')
async def get_invoice(building_id: str, invoice_number: str):
    """
        **get_invoice**
            why is
            used for temporarily holding invoice links for invoices sent as emails
            the links should expire after one day
    :param building_id:
    :param invoice_number:
    :return:
    """
    # TODO move this to invoices
    invoice_number = await invoice_man.get_invoice(invoice_number)
    if invoice_number is None:
        flash(message="Invoice not found - inform your building admin to resend the invoice",
              category="danger")
        return redirect(url_for('home.get_home'), code=302)

    invoice_logger.info(f"Invoice Number : {invoice_number}")
    invoice: Invoice = await lease_agreement_controller.get_invoice(invoice_number=invoice_number)
    if invoice is None:
        invoice_logger.info('did not find invoice')
        flash(message="Error Reading Invoice Issuer Data - Inform the building manager to resend the invoice",
              category="danger")
        return redirect(url_for('home.get_home'), code=302)

    building: Property = await company_controller.get_property_by_id_internal(property_id=building_id)
    company_id = building.company_id
    company: Company = await company_controller.get_company_internal(company_id=company_id)
    bank_account = await company_controller.get_bank_account_internal(company_id=company_id)
    if company is None:
        flash(message="Error Reading Invoice Issuer Data", category="danger")
        return redirect(url_for('home.get_home'), code=302)

    if bank_account is None:
        flash(message="Error Reading Invoice Issuer Data", category="danger")
        return redirect(url_for('home.get_home'), code=302)

    context = {'invoice': invoice.dict(), 'company': company.dict(), 'bank_account': bank_account.dict()}
    return render_template("reports/invoice_report.html", **context)


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

    unit_ = await company_controller.get_unit(user=user,
                                              building_id=invoice_data.property_id,
                                              unit_id=invoice_data.unit_id)
    if not unit_:
        invoice_logger.info(f"Unit not found")
        message_dict = dict(message="Invoiced Unit not Found", category="danger")
        return await redirect_to_unit(message_dict)

        # checking if rental amount should be included - remember rental_amount is a checkbox -
        # the actual rental amount is on unit_

    include_rental: bool = invoice_data.rental_amount == "on"
    # NOte; allows user to specify the invoice due date
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


@invoices_route.post('/admin/invoice/edit-invoice')
@login_required
async def edit_invoice(user: User):
    """

    :param user:
    :return:
    """
    try:
        invoice_data: UnitPaymentForm = UnitPaymentForm(**request.form)
        invoice_logger.info(invoice_data.dict())
    except ValidationError as e:
        invoice_logger.error(str(e))
        invoice_logger.error(dict(**request.form))
        message_dict = dict(message="Unable to to locate the invoice", category="danger")
        return await redirect_to_unit(message_dict)

    invoice: Invoice = await lease_agreement_controller.get_invoice(invoice_number=invoice_data.invoice_number)

    context = dict(invoice=invoice.dict(), property_id=invoice_data.property_id)
    return render_template("invoices/modals/edit_invoice.html", **context)


@invoices_route.post('/admin/invoice/update-invoice')
@login_required
async def update_invoice(user: User):
    """

    :param user:
    :return:
    """
    building_id = request.form.get('building_id')
    invoice_number = request.form.get('invoice_number')
    try:
        update_model = InvoiceUpdateModel(**request.form)
    except ValidationError as e:
        invoice_logger.error(str(e))
        return redirect(url_for('invoices.get_invoice',
                                building_id=building_id,
                                invoice_number=invoice_number), code=302)

    invoice: Invoice = await lease_agreement_controller.get_invoice(invoice_number=invoice_number)
    invoice_ = await _update_invoice(invoice=invoice, update_model=update_model)
    _ = await lease_agreement_controller.update_invoice(invoice=invoice_)

    return redirect(url_for('invoices.get_invoice',
                            building_id=building_id,
                            invoice_number=invoice_number), code=302)


async def _update_invoice(invoice, update_model) -> Invoice:
    """
        **_update_invoice**
    :param invoice:
    :param update_model:
    :return:
    """
    invoice.service_name = update_model.service_name
    invoice.description = update_model.description
    invoice.currency = update_model.currency
    invoice.tax_rate = update_model.tax_rate
    return invoice

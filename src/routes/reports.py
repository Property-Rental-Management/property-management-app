from flask import Blueprint, render_template, flash, url_for, redirect

from src.authentication import login_required
from src.database.models.companies import Company
from src.database.models.invoices import Invoice
from src.database.models.properties import Property
from src.database.models.users import User
from src.logger import init_logger
from src.main import lease_agreement_controller, company_controller, invoice_man

reports_route = Blueprint('reports', __name__)

report_logger = init_logger('REPORT LOGGER:')


@reports_route.get('/admin/reports')
@login_required
async def get_reports(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('reports/reports.html', **context)


@reports_route.get('/reports/invoice/<string:building_id>/<string:invoice_number>')
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
    invoice_number = await invoice_man.get_invoice(invoice_number)
    if invoice_number is None:
        flash(message="Invoice not found - inform your building admin to resend the invoice",
              category="danger")
        return redirect(url_for('home.get_home'), code=302)

    report_logger.info(f"Invoice Number : {invoice_number}")
    invoice: Invoice = await lease_agreement_controller.get_invoice(invoice_number=invoice_number)
    if invoice is None:
        report_logger.info('did not find invoice')
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

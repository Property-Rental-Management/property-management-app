from flask import Blueprint, render_template

from src.authentication import login_required
from src.controller.lease_controller import InvoiceManager
from src.database.models.users import User

reports_route = Blueprint('reports', __name__)
invoice_manager = InvoiceManager()


@reports_route.get('/admin/reports')
@login_required
async def get_reports(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('reports/reports.html', **context)


@reports_route.get('/reports/invoice/<string:invoice_number>')
async def get_invoice(invoice_number: str):
    """
        **get_invoice**
            used for temporarily holding invoice links for invoices sent as emails
            the links should expire after one day
    :param invoice_number:
    :return:
    """
    invoice_number = invoice_manager.get_invoice(invoice_number)
    if invoice_number is None:
        pass

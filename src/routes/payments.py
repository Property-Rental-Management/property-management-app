from flask import Blueprint, render_template

from src.authentication import login_required
from src.database.models.users import User

payments_route = Blueprint('payments', __name__)


@payments_route.get('/admin/payments')
@login_required
async def get_payments(user: User):
    user_data = user.dict()
    context = dict(user=user_data)

    return render_template('payments/payments.html', **context)


@payments_route.get('/admin/get-unit-payment/<string:invoice_number>')
@login_required
async def get_unit_payment(user: User):
    """
    **get_unit_payment**
        will return payment form for use in unit payments
    :param user:
    :return:
    """
    pass

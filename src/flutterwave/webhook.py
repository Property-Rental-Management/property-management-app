from flask import Blueprint

flutterwave_route = Blueprint('flutterwave', __name__)


@flutterwave_route.post('/admin/webhooks/flutterwave/<string:secret_id>')
async def flutterwave_hook(secret_id: str):
    """

    :return:
    """

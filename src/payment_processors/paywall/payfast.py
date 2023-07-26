import hashlib

from flask import Flask, request, jsonify


class PayFastAPI:
    def __init__(self):
        self.pay_fast_secret_key = None

    async def authenticate_request(self):
        """
        Authenticate the incoming request from Payfast using the security signature.
        This method should be called before processing any Payfast request to ensure the request is genuine.
        """
        security_signature = request.headers.get('pf_signature')
        if security_signature is None:
            # If the security signature is missing, the request may be forged or tampered with.
            return jsonify({"status": "error", "message": "Invalid request."}), 403

        # Reconstruct the security signature for the incoming request
        # You need to build the signature using the same algorithm used by Payfast
        # For example, using SHA-256:
        sha256 = hashlib.sha256()
        concatenated_params = ''.join(request.form.values())
        sha256.update((concatenated_params + self.pay_fast_secret_key).encode('utf-8'))
        computed_signature = sha256.hexdigest()

        if computed_signature != security_signature:
            # If the computed signature does not match the one sent by Payfast, the request may be tampered with.
            return jsonify({"status": "error", "message": "Invalid signature."}), 403

        # If the security signature matches, the request is genuine, and you can proceed with processing it.
        return True

    def _add_pay_fast_routes(self, app):
        app.add_url_rule('/payfast/subscribe', 'subscribe', self.subscribe, methods=['POST'])
        app.add_url_rule('/payfast/cancel_subscription', 'cancel_subscription', self.cancel_subscription,
                         methods=['POST'])
        app.add_url_rule('/payfast/upgrade_subscription', 'upgrade_subscription', self.upgrade_subscription,
                         methods=['POST'])
        app.add_url_rule('/payfast/check_subscription', 'check_if_subscribed', self.check_if_subscribed,
                         methods=['GET'])

    def init(self, app: Flask):
        """
        """
        self.pay_fast_secret_key = app.config.get('PAY_FAST_SECRET_KEY')
        self._add_pay_fast_routes(app)

    async def subscribe(self):
        """
        Endpoint to handle subscription requests from Payfast.
        This method will be triggered when Payfast sends a subscription request to your application.
        """
        if not await self.authenticate_request():
            return None

        # Process the subscription request from Payfast
        # You can access the request data using `request.form` or `request.json`
        # Process the subscription request and return an appropriate response
        response_data = {
            "status": "success",
            "message": "Subscription successful."
        }
        return jsonify(response_data)

    async def cancel_subscription(self):
        """
        Endpoint to handle subscription cancellation requests from Payfast.
        This method will be triggered when Payfast sends a subscription cancellation request to your application.
        """
        # Process the subscription cancellation request from Payfast
        # You can access the request data using `request.form` or `request.json`
        # Process the cancellation request and return an appropriate response
        if not await self.authenticate_request():
            return None

        response_data = {
            "status": "success",
            "message": "Subscription canceled."
        }
        return jsonify(response_data)

    async def upgrade_subscription(self):
        """
        Endpoint to handle subscription upgrade requests from Payfast.
        This method will be triggered when Payfast sends a subscription upgrade request to your application.
        """
        if not await self.authenticate_request():
            return None

        # Process the subscription upgrade request from Payfast
        # You can access the request data using `request.form` or `request.json`
        # Process the upgrade request and return an appropriate response

        response_data = {
            "status": "success",
            "message": "Subscription upgraded."
        }
        return jsonify(response_data)

    async def check_if_subscribed(self):
        """
        Endpoint to check if a user is subscribed to a service.
        This method will be triggered when Payfast sends a request to check if a user is subscribed.
        """
        if not await self.authenticate_request():
            return None

        # Check if the user is subscribed to the service
        # You can access any required data from the request using `request.args`
        # Perform the subscription status check and return an appropriate response
        user_id = request.args.get('user_id')
        is_subscribed = True  # Perform your logic to check if the user is subscribed or not

        response_data = {
            "status": "success",
            "is_subscribed": is_subscribed
        }
        return jsonify(response_data)

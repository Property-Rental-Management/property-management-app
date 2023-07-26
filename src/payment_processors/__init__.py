from flask import Flask, jsonify, request


class PaymentProcessor:

    def __init__(self):
        pass

    async def authenticate_request(self):
        pass

    def account_valid(self):
        """
            Account is valid if payment was made for the month and successful
        :return:
        """
        pass

    def process_payment(self):
        """

        :return:
        """
        pass

    def rapyd_webhook(self):
        pass

    def _add_rapyd_webhook(self, app):
        app.add_url_rule('/payments/rapyd/subscription/webhook', 'subscribe', self.rapyd_webhook, methods=['POST'])

    def init(self, app: Flask):
        """
        """
        self._add_rapyd_webhook(app)

    async def subscription_created(self):
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

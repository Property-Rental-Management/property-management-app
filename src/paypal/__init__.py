import requests
from flask import Flask

from src.config import config_instance
from src.logger import init_logger


class PayPal:
    def __init__(self):
        self._logger = init_logger(self.__class__.__name__)
        self._sandbox_uri: str = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        self._live_uri: str = "https://api-m.live.paypal.com/v1/oauth2/token"
        self.access_token: str | None = None
        self.nonce: str | None = None
        self.expires_in: str | None = None

    def _create_access_token(self, client_id: str, client_secret: str) -> str:
        """
        Create PayPal access token.
        :param client_id: PayPal client ID.
        :param client_secret: PayPal client secret.
        :return: Access token.
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials"
        }
        response = requests.post(
            self._sandbox_uri,
            auth=(client_id, client_secret),
            headers=headers,
            data=data
        )

        if response.status_code == 200:
            response_data = response.json()
            self.access_token = response_data.get("access_token")
            self.nonce = response_data.get('nonce')
            self.expires_in = response_data.get('expires_in')
            self._logger.info(f"Access Token: {self.access_token} Nonce: {self.nonce}")
            return self.access_token
        else:
            raise Exception(f"Error creating access token: {response.text}")

    def init_app(self, app: Flask):
        paypal_settings = config_instance().PAYPAL_SETTINGS
        self._create_access_token(client_id=paypal_settings.CLIENT_ID, client_secret=paypal_settings.SECRET_KEY)

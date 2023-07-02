from flask import Flask

from pydantic import BaseModel
import resend
from src.config import config_instance

settings = config_instance().EMAIL_SETTINGS


class EmailModel(BaseModel):
    from_: str | None
    to_: str | None
    subject_: str
    html_: str


class SendMail:
    """
        Make this more formal
    """

    def __init__(self):
        self._resend = resend
        self._resend.api_key = settings.RESEND.API_KEY
        self.from_: str | None = settings.RESEND.from_

    def init_app(self, app: Flask):
        pass

    async def send_mail_resend(self, email: EmailModel):
        params = {'from': self.from_ or email.from_, 'to': email.to_, 'subject': email.subject_, 'html': email.html_}
        self._resend.Emails.send(params=params)

from flask import Flask
from flask_bcrypt import Bcrypt


class Encryptor:

    def __init__(self):
        self._bcrypt: Bcrypt | None = None

    def init_app(self, app: Flask):
        if not self._bcrypt:
            self._bcrypt = Bcrypt()
            self._bcrypt.init_app(app=app)

    def create_hash(self, password: str) -> str:
        return self._bcrypt.generate_password_hash(password).decode('utf-8')

    def compare_hashes(self, hash: str, password: str):
        return self._bcrypt.check_password_hash(pw_hash=hash, password=password)


encryptor = Encryptor()

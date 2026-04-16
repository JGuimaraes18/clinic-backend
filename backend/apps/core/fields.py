import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


class EncryptedTextField(models.TextField):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        key = settings.FIELD_ENCRYPTION_KEY.encode()
        self.cipher = Fernet(key)

    def get_prep_value(self, value):
        if value is None:
            return value
        encrypted = self.cipher.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        decrypted = self.cipher.decrypt(
            base64.urlsafe_b64decode(value.encode())
        )
        return decrypted.decode()

    def to_python(self, value):
        return value
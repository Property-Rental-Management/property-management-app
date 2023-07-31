
import uuid
from enum import Enum

from pydantic import BaseModel, Field, Extra

from src.controller.encryptor import encryptor


class UserType(str, Enum):
    ADMIN = 'admin'
    TENANT = 'tenant'


class User(BaseModel):
    """
    Represents the details of a user.

    Attributes:
    - user_id (str): The ID of the user.
    - company_id (str): The ID of the company_id associated with the user.
    - is_tenant (bool): Indicates if the user is a tenant.
    - tenant_id (str): The ID of the tenant associated with the user.
    - user_type (UserType): The type of user.
    - username (str): The username of the user.
    - password (str | None): The password of the user.
    - email (str): The email address of the user.
    - full_name (str): The full name of the user.
    - contact_number (str): The contact number of the user.
    """
    user_id: str
    is_tenant: bool = Field(default=False)
    tenant_id: str | None
    username: str
    password_hash: str
    email: str
    full_name: str | None
    contact_number: str | None
    account_verified: bool = Field(default=False)
    is_system_admin: bool = Field(default=False)

    class Config:
        orm_mode = True

    def __bool__(self) -> bool:
        return bool(self.user_id) and bool(self.username) and bool(self.password_hash)

    def is_login(self, password: str) -> bool:
        """

        :param password:
        :return:
        """
        return encryptor.compare_hashes(hash=self.password_hash, password=password)

    def __eq__(self, other):
        """
        Compare two User instances based on their user_id only.

        :param other: The other User instance to compare.
        :return: True if user_id of both instances is the same, False otherwise.
        """
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id

class CreateUser(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_tenant: bool = Field(default=False)
    tenant_id: str | None
    username: str
    password: str
    email: str
    full_name: str | None
    contact_number: str | None
    account_verified: bool = Field(default=False)
    is_system_admin: bool = Field(default=False)

    @property
    def password_hash(self):
        return encryptor.create_hash(password=self.password)

    def to_dict(self) -> dict[str, str | bool]:
        dict_ = self.dict(exclude={'password'})
        dict_.update(dict(password_hash=self.password_hash))
        print(f"Update User : {dict_}")
        return dict_


class PasswordResetUser(BaseModel):
    user_id: str
    is_tenant: bool
    tenant_id: str | None
    username: str
    password: str
    email: str
    full_name: str | None
    contact_number: str | None
    account_verified: bool = Field(default=False)
    is_system_admin: bool = Field(default=False)

    @property
    def password_hash(self):
        return encryptor.create_hash(password=self.password)

    def to_dict(self) -> dict[str, str | bool]:
        dict_ = self.dict(exclude={'password'})
        dict_.update(dict(password_hash=self.password_hash))
        print(f"Update User : {dict_}")
        return dict_


class UserUpdate(BaseModel):
    user_id: str
    is_tenant: bool | None
    tenant_id: str | None
    username: str
    email: str
    full_name: str | None
    contact_number: str | None
    account_verified: bool = Field(default=False)

    class Config:
        extra = Extra.ignore

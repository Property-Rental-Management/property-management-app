import uuid
from datetime import date

from pydantic import BaseModel, Field, validator


class Tenant(BaseModel):
    """
    Represents a tenant.

    Attributes:
    - tenant_id (str): The unique ID of the tenant.
    - name (str): The name of the tenant.
    - email (str): The email address of the tenant.
    - phone_number (str): The phone number of the tenant.
    - address_id (str): The ID of the address associated with the tenant.
    - lease_start_date (date): The start date of the lease.
    - lease_end_date (date): The end date of the lease.
    """

    tenant_id: str
    address_id: str | None
    name: str
    id_number: str | None
    company_id: str | None
    email: str | None
    cell: str | None
    is_renting: bool
    lease_start_date: date | None
    lease_end_date: date | None

    @classmethod
    @validator("lease_start_date", pre=True)
    def validate_lease_start_date(cls, value):
        if not isinstance(value, date):
            return None
        return value

    @classmethod
    @validator("lease_end_date", pre=True)
    def validate_lease_end_date(cls, value, values):
        if not isinstance(value, date):
            return None

        start_date = values.get("lease_start_date")
        if start_date and value < start_date:
            raise ValueError("Lease end date cannot be less than lease start date")

        return value

    @property
    def lease_period(self):
        if self.lease_start_date and self.lease_end_date:
            return (self.lease_end_date - self.lease_start_date).days
        return None

    def dict(self) -> dict[str, str | int | date]:
        return {
            "tenant_id": self.tenant_id,
            "address_id": self.address_id,
            "name": self.name,
            "id_number": self.id_number,
            "company_id": self.company_id,
            "email": self.email,
            "cell": self.cell,
            "is_renting": self.is_renting,
            "lease_start_date": self.lease_start_date,
            "lease_end_date": self.lease_end_date,
            "lease_period": self.lease_period
        }


class CreateTenant(BaseModel):
    tenant_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="The unique ID of the tenant.")
    address_id: str | None
    name: str
    company_id: str | None
    id_number: str
    email: str
    cell: str
    is_renting: bool = Field(default=False)
    lease_start_date: date | None
    lease_end_date: date | None


class QuotationForm(BaseModel):
    tenant_name: str
    tenant_company: str
    tenant_cell: str
    tenant_email: str
    company: str | None
    building: str | None
    booking_type: str | None
    lease_start_date: date | None = None
    lease_end_date: date | None = None

    @property
    def property_id(self) -> str:
        return self.company


class TenantSendMail(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    subject: str
    message: str


class TenantAddress(BaseModel):
    address_id: str
    street: str
    city: str
    province: str
    country: str
    postal_code: str


class CreateTenantAddress(BaseModel):
    address_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    street: str
    city: str
    province: str
    country: str
    postal_code: str

import uuid
from datetime import date

from pydantic import BaseModel, Field


class LeaseAgreement(BaseModel):
    """
    Represents a lease agreement.

    Attributes:
    - agreement_id (str): The ID of the lease agreement.
    - property_id (str): The ID of the property associated with the agreement.
    - tenant_id (str): The ID of the tenant associated with the agreement.
    - start_date (date): The start date of the lease.
    - end_date (date): The end date of the lease.
    - rent_amount (float): The monthly rent rental_amount.
    - deposit_amount (float): The security deposit rental_amount.
    - is_active (bool): Indicates if the lease agreement is currently active.
    """

    agreement_id: str
    property_id: str
    tenant_id: str
    unit_id: str
    start_date: date
    end_date: date
    rent_amount: int
    deposit_amount: int | None
    is_active: bool
    payment_period: str | None

    @property
    def days_left(self):
        """
            number of days left until lease expiry
        :return:
        """
        today = date.today()
        if today < self.start_date:
            return (self.end_date - self.start_date).days
        elif today > self.end_date:
            return 0
        else:
            return (self.end_date - today).days


class CreateLeaseAgreement(BaseModel):
    agreement_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Agreement ID")
    property_id: str
    tenant_id: str
    unit_id: str
    start_date: date
    end_date: date
    rent_amount: int
    deposit_amount: int
    is_active: bool
    payment_period: str


class LeaseAgreementTemplate(BaseModel):
    """
    Represents a lease agreement template.

    Attributes:
    - template_id (str): The ID of the template.
    - property_id (str): The ID of the property associated with the template.
    - template_name (str): The name of the template.
    - template_text (str): The text content of the lease agreement template.
    - is_default (bool): Indicates if the template is the default template for the property.
    """
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="template ID")
    property_id: str
    template_name: str
    template_text: str
    is_default: bool

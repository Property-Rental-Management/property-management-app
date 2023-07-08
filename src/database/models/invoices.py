import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, Extra, validator


class Customer(BaseModel):
    """
    The Customer class represents a customer and has the following properties:

        Attributes
        - customer_id: A string representing the unique identifier for the customer.
        - name: A string representing the name of the customer.
        - email: A string representing the email address of the customer.
        - tel: A string representing the telephone number of the customer.
    """
    tenant_id: str
    name: str
    email: str
    cell: str

    class Config:
        extra = Extra.ignore


class InvoicedItems(BaseModel):
    """
    The InvoicedItems class represents items that are invoiced and has the following properties:

        Attributes
        - description: A string representing the description of the invoiced item.
        - multiplier: An integer representing the quantity or multiplier of the invoiced item.
        - rental_amount: An integer representing the unit price or rental_amount of the invoiced item.
    """
    property_id: str
    item_number: str
    description: str
    multiplier: int
    amount: int

    @property
    def sub_total(self) -> int:
        return self.amount * self.multiplier

    def dict(self) -> dict[str, str | int]:
        return {
            'property_id': self.property_id,
            'item_number': self.item_number,
            'description': self.description,
            'multiplier': self.multiplier,
            'amount': self.amount,
            'sub_total': self.sub_total
        }

    class Config:
        extra = Extra.ignore


class CreateInvoicedItem(BaseModel):
    item_number: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    description: str
    multiplier: int
    deleted: bool = Field(default=False)


class BillableItem(BaseModel):
    item_number: str
    property_id: str
    description: str
    multiplier: int
    deleted: bool


# noinspection PyMethodParameters
class Invoice(BaseModel):
    """
    Represents an invoice.

    Attributes:
    - invoice_number (str): The invoice number.
    - tenant_id (str): The ID of the tenant associated with the invoice.
    - month (str): The month of the invoice.
    - rental_amount (float): The rental_amount of the invoice.
    - due_date (date): The due date of the invoice.
    - items (list[str]): A list of items included in the invoice.
    """

    invoice_number: int
    service_name: str
    description: str
    currency: str
    customer: Customer
    discount: int = Field(default=0)
    tax_rate: int = Field(default=15)
    date_issued: date
    due_date: date
    charge_ids: list[str]
    invoice_items: list[InvoicedItems]
    invoice_sent: bool
    invoice_printed: bool
    rental_amount: int

    @validator('charge_ids', pre=True)
    def validate_charge_ids(cls, value):
        print(f"value = {value}")
        if isinstance(value, str):
            return value.split(",")
        elif isinstance(value, list):
            return value
        raise ValueError(f"invalid charge_ids {value}")

    @property
    def total_amount(self) -> int:
        return sum(item.sub_total for item in self.invoice_items) + self.rental_amount

    @property
    def total_taxes(self) -> int:
        return int(self.total_amount * (self.tax_rate / 100))

    @property
    def amount_payable(self) -> int:
        return self.total_amount - self.discount - self.total_taxes

    @property
    def days_remaining(self) -> int:
        today = datetime.now().date()
        return (self.due_date - today).days

    @property
    def notes(self) -> str:
        _notes = f"""
        <strong>Thank you for your business!</strong> Payment is expected within {self.days_remaining} days;
        please process this invoice within that time.
        There will be a 5% interest charge per month on late invoices.
        """
        return _notes

    def dict(self):
        return {
            'invoice_number': self.invoice_number,
            'service_name': self.service_name,
            'description': self.description,
            'currency': self.currency,
            'customer': self.customer,
            'discount': self.discount,
            'tax_rate': self.tax_rate,
            'date_issued': self.date_issued,
            'due_date': self.due_date,
            'charge_ids': self.charge_ids,
            'invoice_items': self.invoice_items,
            'invoice_sent': self.invoice_sent,
            'invoice_printed': self.invoice_printed,
            'rental_amount': self.rental_amount,
            'total_amount': self.total_amount,
            'total_taxes': self.total_taxes,
            'amount_payable': self.amount_payable,
            'days_remaining': self.days_remaining,
            'notes': self.notes
        }

    class Config:
        extra = Extra.ignore


class UnitCharge(BaseModel):
    charge_id: str
    property_id: str
    tenant_id: str
    unit_id: str
    item_number: str
    amount: int
    date_of_entry: date
    is_invoiced: bool


class CreateUnitCharge(BaseModel):
    charge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    tenant_id: str
    unit_id: str
    item_number: str
    amount: int
    date_of_entry: date = Field(default_factory=lambda: datetime.now().date())
    is_invoiced: bool = Field(default=False)


class PrintInvoiceForm(BaseModel):
    building_id: str
    unit_id: str
    invoice_number: str


class UnitEMailInvoiceForm(BaseModel):
    unit_id: str
    building_id: str
    email: str
    subject: str
    message: str
    invoice_numbers: list[str]

    @validator("invoice_numbers", pre=True)
    def validate_invoice_numbers(cls, value):
        if isinstance(value, str):
            return value.split(",")
        elif isinstance(value, list):
            return value
        return None


# noinspection PyMethodParameters
from pydantic import Extra, validator


class UnitCreateInvoiceForm(BaseModel):
    property_id: str
    unit_id: str
    tenant_id: str
    charge_ids: list[str] | None
    rental_amount: str | None
    send_invoice: str

    @validator('charge_ids', pre=True)
    def validate_charge_ids(cls, value) -> list[str]:
        if isinstance(value, str):
            return value.split(",")
        return value

    @validator('rental_amount', pre=True)
    def validate_rental_amount(cls, value, values) -> list[str, None]:
        charge_ids = values.get('charge_ids')
        if (value is None) and (charge_ids is None):
            raise ValueError("Either 'charge_ids' or 'rental_amount' must be provided.")
        return value

    class Config:
        extra = Extra.ignore

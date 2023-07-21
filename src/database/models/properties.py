import uuid
from datetime import date

from pydantic import BaseModel, Field, validator, PositiveInt, FutureDate


class Property(BaseModel):
    """
    Represents a property.

    Attributes:
    - property_id (str): The ID of the property.
    - address (Address): The address of the property.
    - property_type (str): The type of the property. Residential, commercial, industrial, agricultural, mixed
    - number_of_units (int): The total number of units in the property.
    - available_units (int): The number of units currently available.
    - amenities (List[str]): The list of amenities available in the property.
    - landlord (str): The name of the landlord.
    - maintenance_contact (str): The contact information for property maintenance.
    - lease_terms (str): The terms and conditions of the lease.
    - description (str): A description of the property.
    - built_year (int): The year the property was built.
    - parking_spots (int): The number of parking spots available in the property.
    """

    property_id: str
    company_id: str
    name: str
    description: str
    address: str | None
    property_type: str
    number_of_units: int | None
    available_units: int | None
    amenities: str
    landlord: str
    maintenance_contact: str
    lease_terms: str  # Monthly, Daily, Hourly
    built_year: PositiveInt
    parking_spots: int


# noinspection PyNestedDecorators
class Unit(BaseModel):
    """
    Represents a unit in a property.

    Attributes:
    - property_id (str): The ID of the property the unit belongs to.
    - unit_id (str): The ID of the unit.
    - is_occupied (bool): Indicates if the unit is currently occupied.
    - rental_amount (int): The rental rental_amount for the unit.
    - tenant_id (str): The ID of the tenant occupying the unit.
    - lease_start_date (date): The start date of the lease for the unit.
    - lease_end_date (date): The end date of the lease for the unit.
    - unit_area (int): The area of the unit in square feet.
    - has_reception (bool): Indicates if the unit has a reception area.
    """

    tenant_id: str | None = Field(default=None)
    property_id: str
    unit_id: str
    unit_number: str
    is_occupied: bool = Field(default=False)
    is_booked: bool = Field(default=False)
    rental_amount: PositiveInt
    lease_start_date: date | None = Field(default=None)
    lease_end_date: FutureDate | None = Field(default=None)
    unit_area: PositiveInt
    has_reception: bool

    @validator('is_occupied', pre=True)
    @classmethod
    def check_is_occupied(cls, value):
        if value is None:
            return False
        return value

    @classmethod
    @validator('is_booked', pre=True)
    def validate_is_booked(cls, value):

        if not isinstance(value, bool):
            return False
        return value

    @classmethod
    @validator('is_occupied', pre=True)
    def validate_is_occupied(cls, value):
        if not isinstance(value, bool):
            return False
        return value

    @property
    def lease_period(self):
        if self.lease_start_date and self.lease_end_date:
            return (self.lease_end_date - self.lease_start_date).days
        return None

    def dict(self):
        return {
            "tenant_id": self.tenant_id,
            "property_id": self.property_id,
            "unit_id": self.unit_id,
            "unit_number": self.unit_number,
            "is_occupied": self.is_occupied,
            "is_booked": self.is_booked,
            "rental_amount": self.rental_amount,
            "lease_start_date": self.lease_start_date,
            "lease_end_date": self.lease_end_date,
            "lease_period": self.lease_period,
            "unit_area": self.unit_area,
            "has_reception": self.has_reception,
        }


class CreateUnitRental(BaseModel):
    tenant_id: str | None = Field(default=None)
    property_id: str
    unit_id: str
    unit_number: str
    is_occupied: bool = Field(default=True)
    is_booked: bool = Field(default=True)
    rental_amount: PositiveInt
    lease_start_date: date | None = Field(default=None)
    lease_end_date: FutureDate | None = Field(default=None)
    unit_area: PositiveInt
    has_reception: bool
    rental_period: str
    number_days: str | None


class AddUnit(BaseModel):
    property_id: str
    unit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    unit_number: str
    rental_amount: PositiveInt
    unit_area: PositiveInt
    has_reception: bool
    is_booked: bool = Field(default=False)
    is_occupied: bool = Field(default=False)

    @classmethod
    @validator('is_booked', pre=True)
    def validate_is_booked(cls, value):

        if not isinstance(value, bool):
            return False
        return value

    @classmethod
    @validator('is_occupied', pre=True)
    def validate_is_occupied(cls, value):
        if not isinstance(value, bool):
            return False
        return value


class UpdateUnit(BaseModel):
    tenant_id: str
    property_id: str
    unit_id: str
    unit_number: str
    is_occupied: bool | None
    is_booked: bool | None
    rental_amount: PositiveInt
    lease_start_date: date
    lease_end_date: FutureDate
    unit_area: PositiveInt
    has_reception: bool


class UpdateProperty(BaseModel):
    property_id: str
    company_id: str
    name: str
    description: str | None
    address: str | None
    property_type: str | None
    amenities: str | None
    landlord: str | None
    maintenance_contact: str | None
    lease_terms: str | None
    built_year: PositiveInt | None
    parking_spots: int | None


class CreateProperty(BaseModel):
    property_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Property ID")
    company_id: str | None
    name: str
    property_type: str
    number_of_units: int | None
    available_units: int | None
    amenities: str
    landlord: str
    maintenance_contact: str
    lease_terms: str
    description: str
    built_year: PositiveInt
    parking_spots: int

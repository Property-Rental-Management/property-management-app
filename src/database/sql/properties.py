from datetime import date

from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, inspect

from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class PropertyORM(Base):
    __tablename__ = 'properties'

    property_id: str = Column(String(ID_LEN), primary_key=True)
    company_id: str = Column(String(ID_LEN), index=True)
    address: str = Column(String(255))
    name: str = Column(String(NAME_LEN))
    property_type: str = Column(String(NAME_LEN))
    number_of_units: int = Column(Integer, default=0)
    available_units: int = Column(Integer, default=0)
    amenities: str = Column(String(255))
    landlord: str = Column(String(64))
    maintenance_contact: str = Column(String(64))
    lease_terms: str = Column(Text)
    description: str = Column(Text)
    built_year: int = Column(Integer)
    parking_spots: int = Column(Integer)

    def to_dict(self) -> dict[str, str]:
        return {
            'property_id': self.property_id,
            'company_id': self.company_id,
            'name': self.name,
            'address': self.address,
            'property_type': self.property_type,
            'number_of_units': self.number_of_units,
            'available_units': self.available_units,
            'amenities': self.amenities,
            'landlord': self.landlord,
            'maintenance_contact': self.maintenance_contact,
            'lease_terms': self.lease_terms,
            'description': self.description,
            'built_year': self.built_year,
            'parking_spots': self.parking_spots
        }

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)


class UnitORM(Base):
    __tablename__ = 'units'

    unit_id: str = Column(String(ID_LEN), primary_key=True)
    unit_number: str = Column(String(ID_LEN))
    property_id: str = Column(String(ID_LEN), ForeignKey('properties.property_id'))
    tenant_id: str = Column(String(ID_LEN), ForeignKey('tenants.tenant_id'))
    is_occupied: bool = Column(Boolean, default=False)
    is_booked: bool = Column(Boolean, default=False)
    rental_amount: int = Column(Integer)
    lease_start_date: date = Column(Date)
    lease_end_date: date = Column(Date)
    unit_area: int = Column(Integer)
    has_reception: bool = Column(Boolean)

    def to_dict(self) -> dict[str, str]:
        """
        Convert the UnitORM object to a dictionary.
        :return: Dictionary representation of the object.
        """
        return {'unit_id': self.unit_id, 'unit_number': self.unit_number, 'property_id': self.property_id,
                'tenant_id': self.tenant_id,
                'is_occupied': self.is_occupied, 'is_booked': self.is_booked, 'rental_amount': self.rental_amount,
                'unit_area': self.unit_area, 'has_reception': self.has_reception,
                'lease_start_date': self.lease_start_date if self.lease_start_date else None,
                'lease_end_date': self.lease_end_date if self.lease_end_date else None}

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

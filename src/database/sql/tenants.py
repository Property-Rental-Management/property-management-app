from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, inspect
from datetime import date
from src.database.constants import ID_LEN, NAME_LEN
from src.database.sql import Base, engine


class TenantORM(Base):
    __tablename__ = 'tenants'

    tenant_id: str = Column(String(ID_LEN), primary_key=True)
    address_id: str = Column(String(ID_LEN), nullable=True)
    company_id: str = Column(String(ID_LEN), nullable=True)
    name: str = Column(String(NAME_LEN))
    id_number: str = Column(String(13))
    email: str = Column(String(256))
    cell: str = Column(String(13))
    is_renting: bool = Column(Boolean, default=False)
    lease_start_date: date = Column(Date, nullable=True)
    lease_end_date: date = Column(Date, nullable=True)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self):
        """
        Convert the TenantORM object to a dictionary.

        :return: A dictionary representation of the object.
        """
        return {
            'tenant_id': self.tenant_id,
            'address_id': self.address_id,
            'company_id': self.company_id,
            'name': self.name,
            'id_number': self.id_number,
            'email': self.email,
            'cell': self.cell,
            'is_renting': self.is_renting,
            'lease_start_date': self.lease_start_date,
            'lease_end_date': self.lease_end_date
        }


class TenantAddressORM(Base):
    __tablename__ = 'tenants_address'
    address_id: str = Column(String(ID_LEN), primary_key=True)
    street: str = Column(String(NAME_LEN))
    city: str = Column(String(NAME_LEN))
    province: str = Column(String(NAME_LEN))
    country: str = Column(String(NAME_LEN))
    postal_code: str = Column(String(NAME_LEN))

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self) -> dict[str, str]:
        return {
            'address_id': self.address_id,
            'street': self.street,
            'city': self.city,
            'province': self.province,
            'country': self.country,
            'postal_code': self.postal_code
        }

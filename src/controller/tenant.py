from pydantic import ValidationError

from src.controller import error_handler
from src.database.models.properties import Unit, Property
from src.database.models.tenants import Tenant, QuotationForm, CreateTenant, TenantAddress, CreateTenantAddress
from src.database.models.users import User
from src.database.sql import Session
from src.database.sql.tenants import TenantORM, TenantAddressORM
from src.logger import init_logger
from src.main import company_controller


class TenantController:
    def __init__(self):
        self._logger = init_logger(self.__class__.__name__)

    @error_handler
    async def get_tenants_by_company_id(self, company_id: str) -> list[Tenant]:
        """
            **get_tenants_by_company_id**
                this function takes company_id and then obtains Tenant Data of the tenants belonging
                to the properties under the company

        :param company_id:
        :return:
        """
        with Session() as session:

            tenants_list: list[TenantORM] = session.query(TenantORM).filter(TenantORM.company_id == company_id).all()
            try:
                _tenants_list = [Tenant(**tenant_orm.to_dict()) for tenant_orm
                                 in tenants_list if isinstance(tenant_orm, TenantORM)] if tenants_list else []

            except ValidationError as e:
                self._logger.error(str(e))
                pass

            return _tenants_list

    @error_handler
    async def get_tenant_by_cell(self, user: User, cell: str) -> Tenant | None:
        """

        :param user:
        :param cell:
        :return:
        """
        with Session() as session:
            tenant = session.query(TenantORM).filter(TenantORM.cell == cell).first()
            try:
                tenant_data = Tenant(**tenant.to_dict()) if isinstance(tenant, TenantORM) else None
            except ValidationError as e:
                self._logger.error(str(e))
            return tenant_data

    @error_handler
    async def get_tenant_by_id(self, tenant_id: str) -> Tenant | None:
        """

        :param tenant_id:
        :return:
        """
        with Session() as session:
            tenant = session.query(TenantORM).filter(TenantORM.tenant_id == tenant_id).first()
            try:
                tenant_data = Tenant(**tenant.to_dict()) if isinstance(tenant, TenantORM) else None
            except ValidationError as e:
                self._logger.error(str(e))

            return tenant_data

    @error_handler
    async def get_un_booked_tenants(self) -> list[Tenant]:
        with Session() as session:
            tenants_list: list[TenantORM] = session.query(TenantORM).filter(TenantORM.is_renting == False).all()
            try:
                tenant_list = [Tenant(**tenant.to_dict()) for tenant in tenants_list if tenant] if tenants_list else []
            except ValidationError as e:
                self._logger.error(str(e))
            return tenant_list

    @error_handler
    async def create_quotation(self, user: User, quotation: QuotationForm) -> dict[str, Unit | Property]:
        """
        **create_quotation**

        :param user:
        :param quotation:
        :return:
        """
        self._logger.info(f"Creating Quotation with : {quotation}")

        property_listed: Property = await company_controller.get_property(user=user, property_id=quotation.property_id)
        property_units: list[Unit] = await company_controller.get_un_leased_units(
            user=user, property_id=quotation.building)
        # TODO - create a smarter recommendation algorithm for quotations
        min_rental_unit: Unit = min(property_units, key=lambda unit: unit.rental_amount)
        max_rental_unit: Unit = max(property_units, key=lambda unit: unit.rental_amount)

        quote: dict[str, Unit | Property] = {'recommended_unit': min_rental_unit,
                                             'alternate_unit': max_rental_unit,
                                             'property': property_listed}

        return quote

    @error_handler
    async def create_tenant(self, user_id: str, tenant: CreateTenant) -> Tenant:
        """

        :param user_id:
        :param tenant:
        :return:
        """
        with Session() as session:
            tenant_orm: TenantORM = TenantORM(**tenant.dict())
            session.add(tenant_orm)
            session.commit()
            try:
                tenant_data = Tenant(**tenant_orm.to_dict()) if isinstance(tenant_orm, TenantORM) else None
            except ValidationError as e:
                self._logger.error(str(e))

            return tenant_data

    @error_handler
    async def update_tenant(self, tenant: Tenant) -> Tenant | None:
        with Session() as session:
            tenant_orm: TenantORM = session.query(TenantORM).filter(TenantORM.tenant_id == tenant.tenant_id).first()

            if tenant_orm:
                # Update the fields in tenant_orm based on the values in tenant
                for field in tenant.__dict__:
                    if field in tenant_orm.__dict__ and tenant.__dict__[field] is not None:
                        setattr(tenant_orm, field, tenant.__dict__[field])
                session.add(tenant_orm)
                # Commit the changes to the database
                session.commit()
                session.refresh(tenant_orm)
                try:
                    tenant_data = Tenant(**tenant_orm.to_dict()) if isinstance(tenant_orm, TenantORM) else None
                except ValidationError as e:
                    self._logger.error(str(e))
            return tenant_data

    @error_handler
    async def get_tenant_address(self, address_id: str) -> TenantAddress:
        """
            **get_tenant_address**
        :param address_id:
        :return:
        """
        with Session() as session:
            tenant_address_orm: TenantAddressORM = session.query(TenantAddressORM).filter(
                TenantAddressORM.address_id == address_id).first()
            try:
                tenant_address: TenantAddress = TenantAddress(**tenant_address_orm.to_dict()) if isinstance(
                    tenant_address_orm, TenantAddressORM) else None
            except ValidationError as e:
                self._logger.error(str(e))
                return None

            return tenant_address

    @error_handler
    async def create_tenant_address(self, tenant_id: str, tenant_address: CreateTenantAddress) -> TenantAddress | None:
        """

        :param tenant_id:
        :param tenant_address:
        :return:
        """
        with Session() as session:
            tenant_address_orm = TenantAddressORM(**tenant_address.dict())
            session.add(tenant_address_orm)
            session.commit()
            return TenantAddress(**tenant_address.dict())

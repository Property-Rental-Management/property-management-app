from flask import Flask
from pydantic import ValidationError

from src.controller import error_handler, Controllers
from src.database.models.properties import Unit, Property
from src.database.models.tenants import Tenant, QuotationForm, CreateTenant, TenantAddress, CreateTenantAddress
from src.database.models.users import User
from src.database.sql.tenants import TenantORM, TenantAddressORM


class TenantController(Controllers):
    def __init__(self):
        super().__init__()
        self.tenants: list[Tenant] = []

    def manage_tenant_list(self, tenant_instance: Tenant):
        # Check if the tenant instance already exists in the list
        for index, tenant in enumerate(self.tenants):
            if tenant.tenant_id == tenant_instance.tenant_id:
                # Tenant already exists, remove the existing instance
                self.tenants.pop(index)
                self.tenants.append(tenant_instance)
                break
        else:
            # Tenant instance not found, add the new instance to the list
            self.tenants.append(tenant_instance)

    def load_tenants(self) -> None:
        """

        **load_tenants*8

        :return:
        """
        with self.get_session() as session:
            tenant_orm_list = session.query(TenantORM).filter().all()
            try:
                self.tenants = [Tenant(**tenant.to_dict()) for tenant in tenant_orm_list if
                                tenant] if tenant_orm_list else []
            except ValidationError as e:
                self.logger.error(f"Error loading tenants on start_up : {str(e)}")
                pass

    def init_app(self, app: Flask):
        """
        **init_app**
        :param app:
        :return:
        """
        super().init_app(app=app)
        self.load_tenants()

    @error_handler
    async def get_tenants_by_company_id(self, company_id: str) -> list[Tenant]:
        """
            **get_tenants_by_company_id**
                this function takes company_id and then obtains Tenant Data of the tenants belonging
                to the properties under the company
        :param company_id:
        :return:
        """
        if self.tenants:
            return [tenant for tenant in self.tenants if tenant.company_id == company_id]

        with self.get_session() as session:
            tenants_list: list[TenantORM] = session.query(TenantORM).filter(TenantORM.company_id == company_id).all()
            return [Tenant(**tenant_orm.to_dict()) for tenant_orm in tenants_list
                    if isinstance(tenant_orm, TenantORM)] if tenants_list else []

    # noinspection DuplicatedCode
    @error_handler
    async def get_tenant_by_cell(self, user: User, cell: str) -> Tenant | None:
        """

        :param user:
        :param cell:
        :return:
        """
        if self.tenants:
            return next((tenant for tenant in self.tenants if tenant.cell == cell), None)

        with self.get_session() as session:
            tenant = session.query(TenantORM).filter(TenantORM.cell == cell).first()
            return Tenant(**tenant.to_dict()) if isinstance(tenant, TenantORM) else None

    # noinspection DuplicatedCode
    @error_handler
    async def get_tenant_by_id(self, tenant_id: str) -> Tenant | None:
        """
        :param tenant_id:
        :return:
        """
        if self.tenants:
            return next((tenant for tenant in self.tenants if tenant.tenant_id == tenant_id), None)

        with self.get_session() as session:
            tenant = session.query(TenantORM).filter(TenantORM.tenant_id == tenant_id).first()
            return Tenant(**tenant.to_dict()) if isinstance(tenant, TenantORM) else None

    @error_handler
    async def get_un_booked_tenants(self) -> list[Tenant]:
        if self.tenants:
            return [tenant for tenant in self.tenants if not tenant.is_renting]

        with self.get_session() as session:
            tenants_list: list[TenantORM] = session.query(TenantORM).filter(TenantORM.is_renting == False).all()
            return [Tenant(**tenant.to_dict()) for tenant in tenants_list if tenant] if tenants_list else []

    @error_handler
    async def create_quotation(self, user: User, quotation: QuotationForm) -> dict[str, Unit | Property]:
        """
        **create_quotation**
        # DEPRECATED
        :param user:
        :param quotation:
        :return:
        """
        from src.main import company_controller
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
        with self.get_session() as session:
            tenant_orm: TenantORM = TenantORM(**tenant.dict())
            tenant_data = Tenant(**tenant_orm.to_dict()) if isinstance(tenant_orm, TenantORM) else None
            self.tenants.append(tenant_data)
            session.add(tenant_orm)
            session.commit()
            return tenant_data

    @error_handler
    async def update_tenant(self, tenant: Tenant) -> Tenant | None:
        with self.get_session() as session:
            tenant_orm: TenantORM = session.query(TenantORM).filter(TenantORM.tenant_id == tenant.tenant_id).first()

            if tenant_orm:
                fields_to_update = [field for field in tenant_orm.__dict__.keys() if not field.startswith("_")]

                for field in fields_to_update:
                    if hasattr(tenant, field) and getattr(tenant, field) is not None:
                        setattr(tenant_orm, field, getattr(tenant, field))

                session.merge(tenant_orm)
                session.commit()
                tenant = Tenant(**tenant_orm.to_dict())
                # NOTE Update the tenant record in self.tenants
                self.manage_tenant_list(tenant_instance=tenant)
                return tenant

        return None

    @error_handler
    async def get_tenant_address(self, address_id: str) -> TenantAddress:
        """
            **get_tenant_address**
        :param address_id:
        :return:
        """
        with self.get_session() as session:
            tenant_address_orm: TenantAddressORM = session.query(TenantAddressORM).filter(
                TenantAddressORM.address_id == address_id).first()
            return TenantAddress(**tenant_address_orm.to_dict()) if isinstance(
                tenant_address_orm, TenantAddressORM) else None

    @error_handler
    async def create_tenant_address(self, tenant_id: str, tenant_address: CreateTenantAddress) -> TenantAddress | None:
        """

        :param tenant_id:
        :param tenant_address:
        :return:
        """
        with self.get_session() as session:
            tenant_address_orm = TenantAddressORM(**tenant_address.dict())
            session.add(tenant_address_orm)
            session.commit()
            return TenantAddress(**tenant_address.dict())

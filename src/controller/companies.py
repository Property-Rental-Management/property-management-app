import uuid

from flask import Flask
from pydantic import ValidationError

from src.controller import error_handler, UnauthorizedError, Controllers
from src.database.models.bank_accounts import BusinessBankAccount
from src.database.models.companies import (Company, UpdateCompany, TenantRelationCompany, CreateTenantCompany,
                                           UpdateTenantCompany, UserRelationCompany)
from src.database.models.invoices import CreateInvoicedItem, BillableItem, CreateUnitCharge
from src.database.models.properties import Property, Unit, AddUnit, UpdateProperty, CreateProperty
from src.database.models.users import User
from src.database.sql.bank_account import BankAccountORM
from src.database.sql.companies import CompanyORM, UserCompanyORM, TenantCompanyORM
from src.database.sql.invoices import ItemsORM, UserChargesORM
from src.database.sql.properties import PropertyORM, UnitORM
from src.logger import init_logger


class CompaniesController(Controllers):
    def __init__(self):
        super().__init__()
        self._logger = init_logger(self.__class__.__name__)
        self.company_user: dict[str, str] = {}
        self.company_tenant: dict[str, str] = {}
        self.companies: list[Company] = []
        self.units: list[Unit] = []
        self.buildings: list[Property] = []

    def manage_company_list(self, company_instance: Company):
        # Check if the tenant instance already exists in the list

        for index, company in enumerate(self.companies):
            if company.company_id == company_instance.company_id:
                # Tenant already exists, remove the existing instance
                self.companies.pop(index)
                self.companies.append(company_instance)
                break
        else:
            # Tenant instance not found, add the new instance to the list
            self.companies.append(company_instance)

    def manage_building_list(self, building_instance: Property):
        # Check if the tenant instance already exists in the list

        for index, building in enumerate(self.buildings):
            if building == building_instance:
                # Tenant already exists, remove the existing instance
                self.buildings.pop(index)
                self.buildings.append(building_instance)
                break
        else:
            # Tenant instance not found, add the new instance to the list
            self.buildings.append(building_instance)

    def manage_unit_list(self, unit_instance: Unit):
        # Check if the tenant instance already exists in the list

        for index, unit in enumerate(self.units):
            if unit == unit_instance:
                # Tenant already exists, remove the existing instance
                self.units.pop(index)
                self.units.append(unit_instance)
                break
        else:
            # Tenant instance not found, add the new instance to the list
            self.units.append(unit_instance)

    def load_company_details(self):
        """

        :return:
        """
        with self.get_session() as session:
            user_company_data = session.query(UserCompanyORM).filter().all()
            self.company_user = {user_company.company_id: user_company.user_id for user_company in user_company_data}
            self.companies = [Company(**company.to_dict()) for company in session.query(CompanyORM).filter().all()]
            self.units = [Unit(**unit.to_dict()) for unit in session.query(UnitORM).filter().all()]
            self.buildings = [Property(**building.to_dict()) for building in session.query(PropertyORM).filter().all()]

    def init_app(self, app: Flask):
        self.load_company_details()

    @error_handler
    async def is_company_member(self, user_id: str, company_id: str, session) -> bool:

        if self.company_user and user_id:
            return self.company_user.get(company_id) == user_id

        result: UserCompanyORM = session.query(UserCompanyORM).filter(
            UserCompanyORM.user_id == user_id, UserCompanyORM.company_id == company_id).first()

        return result and result.user_id == user_id

    @error_handler
    async def get_user_companies(self, user_id: str) -> list[Company]:
        if self.company_user and self.company_user:
            # Get the list of company IDs associated with the given user_id
            company_ids = [company_id for company_id, user in self.company_user.items() if user == user_id]
            # Filter the companies list based on the company IDs then return
            return [company for company in self.companies if company.company_id in company_ids]

        with self.get_session() as session:
            company_list: list[UserCompanyORM] = session.query(UserCompanyORM).filter(
                UserCompanyORM.user_id == user_id).all()

            response = []
            for user_company in company_list:
                if isinstance(user_company, UserCompanyORM):
                    company_orm: CompanyORM = session.query(CompanyORM).filter(
                        CompanyORM.company_id == user_company.company_id).first()

                    if isinstance(company_orm, CompanyORM):
                        response.append(Company(**company_orm.to_dict()))

            return response

    @error_handler
    async def get_company(self, company_id: str, user_id: str) -> Company | None:
        with self.get_session() as session:
            _is_company_member: bool = await self.is_company_member(company_id=company_id,
                                                                    user_id=user_id,
                                                                    session=session)
            if not _is_company_member:
                raise UnauthorizedError('You are not authorized to access this company')

            company_orm = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()

            return Company(**company_orm.to_dict()) if isinstance(company_orm, CompanyORM) else None

    # @error_handler
    # async def internal_company_id_to_user_id(self, company_id: str) -> UserCompanyORM:
    #     """
    #         **internal_company_id_to_user_id**
    #     :param company_id:
    #     :return:
    #     """
    #     for company in self.companies:
    #         if company.company_id == company_id:
    #             # Return the UserCompanyORM object if company_id matches
    #             return company
    #
    #     # If company_id does not match any company in self.companies,
    #     # perform the database query
    #     with self.get_session() as session:
    #         user_company = session.query(UserCompanyORM).filter(UserCompanyORM.company_id == company_id).first()
    #
    #     return user_company

    @error_handler
    async def get_company_internal(self, company_id: str) -> Company | None:

        for company in self.companies:
            if company.company_id == company_id:
                return company

        with self.get_session() as session:
            company_orm: CompanyORM = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()
            return Company(**company_orm.to_dict()) if isinstance(company_orm, CompanyORM) else None

    @error_handler
    async def create_company(self, company: Company, user: User) -> Company | None:

        # Perform necessary operations to create the company_id
        # For example, you can save the company_id data in a database
        # and associate it with the user
        with self.get_session() as session:
            # TODO Check if payment is already made
            company_orm: CompanyORM = CompanyORM(**company.dict())

            try:
                company: Company = Company(**company_orm.to_dict()) if isinstance(company_orm, CompanyORM) else None
                self.companies.append(company)
            except ValidationError as e:
                self._logger.error(str(e))
                return None

            user_company_dict = dict(id=str(uuid.uuid4()), company_id=company_orm.company_id, user_id=user.user_id)
            session.add(company_orm)
            user_company_orm: UserCompanyORM = UserCompanyORM(**user_company_dict)
            # Note see cache_dict to understand what is happening here
            self.company_user.update(UserRelationCompany(**user_company_dict).cache_dict())
            session.add(user_company_orm)
            session.commit()
            return company

    @error_handler
    async def create_company_internal(self, company: CreateTenantCompany) -> Company | None:
        """
        **create_company_internal**

        :param company:
        :return:
        """
        with self.get_session() as session:
            company_orm: CompanyORM = CompanyORM(**company.dict())
            result = Company(**company_orm.to_dict()) if isinstance(company_orm, CompanyORM) else None
            session.add(company_orm)
            session.commit()
            self.companies.append(result)
            return result

    @error_handler
    async def create_company_tenant_relation_internal(self,
                                                      company_relation: TenantRelationCompany) -> TenantRelationCompany:
        """
            **create_company_tenant_relation_internal**
        :return:
        """
        with self.get_session() as session:
            tenant_relation_orm: TenantCompanyORM = TenantCompanyORM(**company_relation.dict())
            session.add(tenant_relation_orm)
            session.commit()
            self.company_tenant.update(company_relation.cache_dict())
            return company_relation

    @error_handler
    async def update_company(self, user: User, company_data: UpdateCompany) -> Company | None:
        """
            **update_company**

        :param user:
        :param company_data:
        :return:
        """
        with self.get_session() as session:
            user_id = user.user_id
            company_id = company_data.company_id
            is_company_member: bool = await self.is_company_member(user_id=user_id, company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to Update Bank Account")

            _company_data = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()

            if _company_data is None:
                return None

            # Update original_company_data fields with corresponding values from company_data
            for field, value in company_data.dict().items():
                if value is not None:
                    setattr(_company_data, field, value)

            session.merge(_company_data)
            session.commit()
            company = Company(**_company_data.to_dict())
            self.manage_company_list(company_instance=company)
            return company

    @error_handler
    async def update_tenant_company(self, company_data: UpdateTenantCompany):
        """
            **update_tenant_company**
        :return:
        """
        with self.get_session() as session:
            company_id: str = company_data.company_id
            o_company_data: CompanyORM = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()

            if o_company_data is None:
                return None

            # Update original_company_data fields with corresponding values from company_data
            for field, value in company_data.dict().items():
                if value is not None:
                    setattr(o_company_data, field, value)
            session.merge(o_company_data)
            session.commit()
            update_company_data = Company(**o_company_data.to_dict())
            self.manage_company_list(company_instance=update_company_data)
            return update_company_data

    @error_handler
    async def update_bank_account(self, user: User, account_details: BusinessBankAccount) -> BusinessBankAccount | None:
        """
        **update_bank_account**
            will either update or create a new bank account record
        :return:
        """
        with self.get_session() as session:
            user_id = user.user_id
            company_id = account_details.company_id
            is_company_member: bool = await self.is_company_member(user_id=user_id, company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to Update Bank Account")

            original_bank_account: BankAccountORM = session.query(BankAccountORM).filter(
                BankAccountORM.account_number == account_details.account_number).first()
            if original_bank_account:
                for field, value in account_details.dict().items():
                    if value is not None:
                        setattr(original_bank_account, field, value)
                session.merge(original_bank_account)
                session.commit()
                return BusinessBankAccount(**original_bank_account.to_dict())

            bank_account_orm: BankAccountORM = BankAccountORM(**account_details.dict())
            session.add(bank_account_orm)
            session.commit()

            return account_details

    @error_handler
    async def add_property(self, user: User, _property: CreateProperty) -> Property | None:
        """

        :param user:
        :param _property:
        :return:
        """
        with self.get_session() as session:
            user_id = user.user_id
            company_id = _property.company_id
            is_company_member: bool = await self.is_company_member(user_id=user_id, company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to Add Properties to this Company")

            property_orm: PropertyORM = PropertyORM(**_property.dict())

            building = Property(**property_orm.to_dict()) if isinstance(property_orm, PropertyORM) else None

            self.buildings.append(building)

            session.add(property_orm)
            session.commit()

            return building

    @error_handler
    async def update_property(self, user: User, property_details: UpdateProperty) -> Property | None:
        with self.get_session() as session:
            user_id = user.user_id
            company_id = property_details.company_id
            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to update this Property")

            original_property_orm: PropertyORM = session.query(PropertyORM).filter(
                PropertyORM.property_id == property_details.property_id).first()

            # Create a dictionary of field names and values from the property_details object
            field_updates = {field: getattr(property_details, field) for field in property_details.__fields__}

            # Update the relevant fields in original_property_orm
            for field, value in field_updates.items():
                if value:
                    setattr(original_property_orm, field, value)
                session.merge(original_property_orm)
            # Commit the changes to the database
            session.commit()
            building = Property(**original_property_orm.to_dict()) if isinstance(original_property_orm,
                                                                                 PropertyORM) else None
            if building:
                self.buildings.append(building)
            return building

    @error_handler
    async def get_properties(self, user: User, company_id: str) -> list[Property] | None:
        """

        :param user:
        :param company_id:
        :return:
        """
        if self.buildings:
            return [building for building in self.buildings if building.company_id == company_id]

        with self.get_session() as session:
            # Move this up
            user_id = user.user_id
            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access Properties in this Company")

            properties: list[PropertyORM] = session.query(PropertyORM).filter(
                PropertyORM.company_id == company_id).all()

            return [Property(**_prop.to_dict()) for _prop in properties
                    if isinstance(_prop, PropertyORM)] if properties else []

    @error_handler
    async def get_properties_internal(self, company_id: str) -> list[Property] | None:
        """
            **get_properties_internal**
        :param company_id:
        :return:
        """
        if self.buildings:
            return [building for building in self.buildings if building.company_id == company_id]

        with self.get_session() as session:
            properties: list[PropertyORM] = session.query(PropertyORM).filter(
                PropertyORM.company_id == company_id).all()

            return [Property(**_prop.to_dict()) for _prop in properties
                    if isinstance(_prop, PropertyORM)] if properties else []

    @error_handler
    async def get_property_by_id_internal(self, property_id: str) -> Property | None:
        """

        :param property_id:
        :return:
        """
        for building in self.buildings:
            if building.property_id == property_id:
                return building

        with self.get_session() as session:
            property_: PropertyORM = session.query(PropertyORM).filter(PropertyORM.property_id == property_id).first()
            return Property(**property_.to_dict()) if isinstance(property_, PropertyORM) else None

    @error_handler
    async def user_company_id(self, company_id: str) -> list[UserCompanyORM]:
        """

        :param company_id:
        :return:
        """
        with self.get_session as session:
            users_for_company: list[UserCompanyORM] = session.query(UserCompanyORM).filter(
                UserCompanyORM.company_id == company_id).all()
            return users_for_company

    @error_handler
    async def get_bank_accounts(self, user: User, company_id: str) -> BusinessBankAccount | None:
        """

        :param user:
        :param company_id:
        :return:
        """
        with self.get_session() as session:
            user_id = user.user_id
            is_company_member: bool = await self.is_company_member(user_id=user_id, company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access that Bank Account")

            bank_account: BankAccountORM = session.query(BankAccountORM).filter(
                BankAccountORM.company_id == company_id).first()
            return BusinessBankAccount(**bank_account.to_dict()) if isinstance(bank_account, BankAccountORM) else None

    @error_handler
    async def get_bank_account_internal(self, company_id: str) -> BusinessBankAccount | None:
        """
            **get_bank_account_internal**
        :param company_id:
        :return:
        """
        with self.get_session() as session:
            bank_account: BankAccountORM = session.query(BankAccountORM).filter(
                BankAccountORM.company_id == company_id).first()
            return BusinessBankAccount(**bank_account.to_dict()) if isinstance(bank_account, BankAccountORM) else None

    @error_handler
    async def get_property(self, user: User, property_id: str) -> Property | None:
        """

        :param user:
        :param property_id:
        :return:
        """
        for building in self.buildings:
            if building.property_id == property_id:
                return building

        with self.get_session() as session:
            _property: PropertyORM = session.query(PropertyORM).filter(
                PropertyORM.property_id == property_id).first()

            user_id = user.user_id
            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=_property.company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access the Property")

            return Property(**_property.to_dict()) if isinstance(_property, PropertyORM) else None

    @error_handler
    async def get_property_units(self, user: User, property_id: str) -> list[Unit]:
        """

        :return: False
        """
        if self.units:
            return [unit for unit in self.units if unit.property_id == property_id]

        with self.get_session() as session:
            await self.check_ownership(property_id, session, user)

            property_units: list[UnitORM] = session.query(UnitORM).filter(UnitORM.property_id == property_id).all()
            return [Unit(**unit_.to_dict()) for unit_ in property_units
                    if isinstance(unit_, UnitORM)] if property_units else []

    async def check_ownership(self, property_id, session, user):
        user_id = user.user_id
        _property: PropertyORM = session.query(PropertyORM).filter(
            PropertyORM.property_id == property_id).first()
        is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                               company_id=_property.company_id,
                                                               session=session)
        if not is_company_member:
            raise UnauthorizedError(description="Not Authorized to access the Property")
        return _property

    @error_handler
    async def get_un_leased_units(self, user: User, property_id: str) -> list[Unit]:
        """
            **get_un_leased_units**
                given a property id return all units in the property which are not leased
        :param user:
        :param property_id:
        :return:
        """
        if self.units:
            return [unit for unit in self.units if (unit.property_id == property_id and not unit.is_occupied)]

        with self.get_session() as session:
            _ = await self.check_ownership(property_id=property_id, session=session, user=user)

            property_units: list[UnitORM] = session.query(UnitORM).filter(UnitORM.property_id == property_id,
                                                                          UnitORM.is_occupied == False).all()
            return [Unit(**building.to_dict()) for building
                    in property_units if building] if isinstance(property_units, list) else []

    @error_handler
    async def add_unit(self, user: User, unit_data: AddUnit, property_id: str) -> AddUnit:
        """

        :param user:
        :param property_id:
        :param unit_data:
        :return:
        """
        with self.get_session() as session:
            _property = await self.check_ownership(property_id, session, user)

            # Note Adding one more unit number of units and available units
            _property.number_of_units += 1
            _property.available_units += 1

            unit_orm: UnitORM = UnitORM(**unit_data.dict())
            session.add(unit_orm)
            session.commit()
            self.units.append(Unit(**unit_data.dict()))
            return unit_data

    @error_handler
    async def get_unit(self, user: User, building_id: str, unit_id: str) -> Unit | None:
        """
            **get_unit**
        :param user:
        :param building_id:
        :param unit_id:
        :return:
        """
        # Useless statement
        for unit in self.units:
            if unit.property_id == building_id and unit.unit_id == unit_id:
                return unit

        _ = user.dict()
        with self.get_session() as session:
            unit_data: UnitORM = session.query(UnitORM).filter(
                UnitORM.property_id == building_id, UnitORM.unit_id == unit_id).first()
            if unit_data is None:
                return None
            return Unit(**unit_data.to_dict()) if isinstance(unit_data, UnitORM) else None

    @error_handler
    async def update_unit(self, user_id: str, unit_data: Unit) -> Unit | None:
        """

        :param user_id:
        :param unit_data:
        :return:
        """
        with self.get_session() as session:
            unit_orm: UnitORM = session.query(UnitORM).filter(UnitORM.unit_id == unit_data.unit_id,
                                                              UnitORM.property_id == unit_data.property_id).first()

            if unit_orm:
                fields_to_update = [field for field in unit_orm.__dict__.keys() if not field.startswith("_")]

                for field in fields_to_update:
                    if getattr(unit_data, field, None) is not None:
                        setattr(unit_orm, field, getattr(unit_data, field))

                # Commit the changes to the database
                session.merge(unit_orm)
                session.commit()
                unit_data = Unit(**unit_orm.to_dict())
                self.manage_unit_list(unit_instance=unit_data)
                return unit_data

            return None

    @error_handler
    async def create_billable_item(self, billable_item: CreateInvoicedItem) -> CreateInvoicedItem:
        """
        **create_billable_item**

        :param billable_item:
        :return:
        """
        with self.get_session() as session:
            billable_orm: ItemsORM = ItemsORM(**billable_item.dict())
            session.add(billable_orm)
            session.commit()
            return billable_item

    @error_handler
    async def get_billed_item(self, property_id: str, item_number: str):
        with self.get_session() as session:
            billable_orm: ItemsORM = session.query(ItemsORM).filter(ItemsORM.property_id == property_id,
                                                                    ItemsORM.item_number == item_number).first()
            return CreateInvoicedItem(**billable_orm.to_dict())

    @error_handler
    async def delete_billed_item(self, property_id: str, item_number: str):
        """
        **delete_billed_item**
        :param property_id:
        :param item_number:
        :return:
        """
        with self.get_session() as session:
            billable_orm: ItemsORM = session.query(ItemsORM).filter(ItemsORM.property_id == property_id,
                                                                    ItemsORM.item_number == item_number).first()
            billable_orm.deleted = True
            session.merge(billable_orm)
            session.commit()
            return CreateInvoicedItem(**billable_orm.to_dict()) if isinstance(billable_orm, ItemsORM) else None

    @error_handler
    async def get_billable_items(self, building_id: str) -> list[BillableItem]:
        """
            **get_billable_items**
        :param building_id:
        :return:
        """
        with self.get_session() as session:
            billable_list: list[ItemsORM] = session.query(ItemsORM).filter(ItemsORM.property_id == building_id,
                                                                           ItemsORM.deleted == False).all()
            return [BillableItem(**item.to_dict()) for item in billable_list
                    if isinstance(item, ItemsORM)] if billable_list else []

    @error_handler
    async def create_unit_bill_charge(self, charge_item: CreateUnitCharge) -> CreateUnitCharge:
        """
            **create_unit_bill_charge**
        :param charge_item:
        :return:
        """
        with self.get_session() as session:
            charge_item_orm: UserChargesORM = UserChargesORM(**charge_item.dict())
            session.add(charge_item_orm)
            session.commit()
            return charge_item

    @error_handler
    async def delete_unit_charge(self, charge_id: str) -> CreateUnitCharge:
        """

        :return:
        """
        with self.get_session() as session:
            charge_item_orm: UserChargesORM = session.query(UserChargesORM).filter(
                UserChargesORM.charge_id == charge_id).first()
            _unit_charge = CreateUnitCharge(**charge_item_orm.to_dict())
            if charge_item_orm:
                session.delete(charge_item_orm)
                session.commit()
            return _unit_charge

    @error_handler
    async def get_charged_items(self, building_id: str, unit_id: str):
        """

        :param building_id:
        :param unit_id:
        :return:
        """
        with self.get_session() as session:
            charged_items: list[UserChargesORM] = session.query(UserChargesORM).filter(
                UserChargesORM.property_id == building_id,
                UserChargesORM.unit_id == unit_id,
                UserChargesORM.is_invoiced == False).all()
            return [CreateUnitCharge(**charge.to_dict()) for charge in charged_items
                    if isinstance(charge, UserChargesORM)] if charged_items else []

    @error_handler
    async def get_item_by_number(self, item_number: str) -> BillableItem:
        """

        :param item_number:
        :return:
        """
        with self.get_session() as session:
            billable_item: ItemsORM = session.query(ItemsORM).filter(ItemsORM.item_number == item_number).first()
            return BillableItem(**billable_item.to_dict())

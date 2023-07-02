import uuid

from pydantic import ValidationError

from src.database.sql.invoices import ItemsORM, UserChargesORM
from src.database.models.invoices import CreateInvoicedItem, BillableItem, CreateUnitCharge
from src.database.sql.bank_account import BankAccountORM
from src.database.models.bank_accounts import BusinessBankAccount
from src.database.models.properties import Property, Unit, AddUnit, UpdateProperty, CreateProperty
from src.database.sql.properties import PropertyORM, UnitORM
from src.database.sql import Session
from src.database.models.users import User
from src.database.models.companies import Company, UpdateCompany, TenantRelationCompany, CreateTenantCompany, \
    UpdateTenantCompany
from src.database.sql.companies import CompanyORM, UserCompanyORM, TenantCompanyORM
from src.controller import error_handler, UnauthorizedError


class CompaniesController:
    def __init__(self):
        pass

    @error_handler
    async def is_company_member(self, user_id: str, company_id: str, session):
        result: UserCompanyORM = session.query(UserCompanyORM).filter(
            UserCompanyORM.user_id == user_id, UserCompanyORM.company_id == company_id).first()
        return isinstance(result, UserCompanyORM)

    @staticmethod
    @error_handler
    async def get_user_companies(user_id: str) -> list[Company]:
        with Session() as session:
            user_company_list = session.query(UserCompanyORM).filter(UserCompanyORM.user_id == user_id).all()

            response = []
            for user_company in user_company_list:
                if isinstance(user_company, UserCompanyORM):
                    company_orm = session.query(CompanyORM).filter(
                        CompanyORM.company_id == user_company.company_id).first()
                    if isinstance(company_orm, CompanyORM):
                        response.append(Company(**company_orm.to_dict()))

            return response

    @error_handler
    async def get_company(self, company_id: str, user_id: str) -> Company | None:
        with Session() as session:
            _is_company_member: bool = await self.is_company_member(company_id=company_id,
                                                                    user_id=user_id,
                                                                    session=session)
            if not _is_company_member:
                raise UnauthorizedError('You are not authorized to access this company_id')

            company_orm = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()
            return Company(**company_orm.to_dict()) if company_orm else None

    @error_handler
    async def internal_company_id_to_user_id(self, company_id: str) -> UserCompanyORM:
        """

        :param company_id:
        :return:
        """
        with Session() as session:
            user_company: UserCompanyORM = session.query(UserCompanyORM).filter(
                UserCompanyORM.company_id == company_id).filter()
            return user_company

    @staticmethod
    @error_handler
    async def get_company_internal(company_id: str) -> Company | None:
        with Session() as session:
            company_orm = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()
            try:
                company_data: Company | None = Company(**company_orm.to_dict()) if company_orm else None
            except ValidationError:
                pass

            return company_data

    @staticmethod
    @error_handler
    async def create_company(company: Company, user: User) -> Company:
        # Perform necessary operations to create the company_id
        # For example, you can save the company_id data in a database
        # and associate it with the user
        with Session() as session:
            # TODO Check if payment is already made
            company_orm: CompanyORM = CompanyORM(**company.dict())
            response = Company(**company_orm.to_dict())
            user_company_data = dict(id=str(uuid.uuid4()), company_id=company_orm.company_id, user_id=user.user_id)
            session.add(company_orm)
            session.add(UserCompanyORM(**user_company_data))
            session.commit()

            return response

    @staticmethod
    @error_handler
    async def create_company_internal(company: CreateTenantCompany) -> Company:
        """

        :param company:
        :return:
        """
        with Session() as session:
            _company = Company(**company.dict())
            company_orm: CompanyORM = CompanyORM(**_company.dict())
            session.add(company_orm)
            session.commit()
            return company

    @staticmethod
    @error_handler
    async def create_company_tenant_relation_internal(company_relation: TenantRelationCompany) -> TenantRelationCompany:
        """

        :return:
        """
        with Session() as session:
            company_tenant_relation_orm: TenantCompanyORM = TenantCompanyORM(**company_relation.dict())
            session.add(company_tenant_relation_orm)
            session.commit()
            return company_relation

    @error_handler
    async def update_company(self, user: User, company_data: UpdateCompany):
        """

        :param user:
        :param company_data:
        :return:
        """
        with Session() as session:
            user_id = user.user_id
            company_id = company_data.company_id
            is_company_member: bool = await self.is_company_member(user_id=user_id, company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to Update Bank Account")
            original_company_data: CompanyORM = session.query(CompanyORM).filter(
                CompanyORM.company_id == company_id).first()

            if original_company_data is None:
                return None

            # Update original_company_data fields with corresponding values from company_data
            for field, value in company_data.dict().items():
                if value is not None:
                    setattr(original_company_data, field, value)
            session.commit()

            return UpdateCompany(**original_company_data.to_dict())

    @error_handler
    async def update_tenant_company(self, company_data: UpdateTenantCompany):
        """

        :return:
        """
        with Session() as session:
            company_id: str = company_data.company_id
            o_company_data: CompanyORM = session.query(CompanyORM).filter(CompanyORM.company_id == company_id).first()

            if o_company_data is None:
                return None

            # Update original_company_data fields with corresponding values from company_data
            for field, value in company_data.dict().items():
                if value is not None:
                    setattr(o_company_data, field, value)
            session.commit()
            return company_data


    @error_handler
    async def update_bank_account(self, user: User, account_details: BusinessBankAccount) -> BusinessBankAccount | None:
        """
        **update_bank_account**
            will either update or create a new bank account record
        :return:
        """
        with Session() as session:
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
        with Session() as session:
            user_id = user.user_id
            company_id = _property.company_id
            is_company_member: bool = await self.is_company_member(user_id=user_id, company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to Add Properties to this Company")

            property_orm: PropertyORM = PropertyORM(**_property.dict())
            session.add(property_orm)
            session.commit()
            return _property

    @error_handler
    async def update_property(self, user: User, property_details: UpdateProperty) -> Property | None:
        with Session() as session:
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

            # Commit the changes to the database
            session.commit()
            return Property(**original_property_orm.to_dict())

    @error_handler
    async def get_properties(self, user: User, company_id: str) -> list[Property]:
        """

        :param user:
        :param company_id:
        :return:
        """
        with Session() as session:
            user_id = user.user_id
            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access Properties in this Company")

            properties: list[PropertyORM] = session.query(PropertyORM).filter(
                PropertyORM.company_id == company_id).all()
            return [Property(**_prop.to_dict()) for _prop in properties]

    @error_handler
    async def get_property_by_id_internal(self, property_id: str) -> Property:
        """

        :param property_id:
        :return:
        """
        with Session() as session:
            property_: PropertyORM = session.query(PropertyORM).filter(PropertyORM.property_id == property_id).first()
            return Property(**property_.to_dict())

    @staticmethod
    @error_handler
    async def user_company_id(company_id: str) -> list[UserCompanyORM]:
        """

        :param company_id:
        :return:
        """
        with Session() as session:
            users_for_company: list[UserCompanyORM] = session.query(UserCompanyORM).filter(
                UserCompanyORM.company_id == company_id).all()
            return users_for_company

    @error_handler
    async def get_bank_accounts(self, user: User, company_id: str) -> BusinessBankAccount:
        """

        :param user:
        :param company_id:
        :return:
        """
        with Session() as session:
            user_id = user.user_id
            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access that Bank Account")

            bank_account: BankAccountORM = session.query(BankAccountORM).filter(
                BankAccountORM.company_id == company_id).first()

            return BusinessBankAccount(**bank_account.to_dict())

    @error_handler
    async def get_property(self, user: User, property_id: str) -> Property:
        """

        :param user:
        :param property_id:
        :return:
        """
        with Session() as session:
            _property: PropertyORM = session.query(PropertyORM).filter(
                PropertyORM.property_id == property_id).first()

            user_id = user.user_id
            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=_property.company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access the Property")

            return Property(**_property.to_dict())

    @error_handler
    async def get_property_units(self, user: User, property_id: str) -> list[Unit]:
        """

        :return: False
        """
        with Session() as session:
            user_id = user.user_id

            _property: PropertyORM = session.query(PropertyORM).filter(
                PropertyORM.property_id == property_id).first()

            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=_property.company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access the Property")

            property_units: list[UnitORM] = session.query(UnitORM).filter(UnitORM.property_id == property_id).all()
            return [Unit(**prop.to_dict()) for prop in property_units]

    @error_handler
    async def get_un_leased_units(self, user: User, property_id: str) -> list[Unit]:
        """
            **get_un_leased_units**
                given a property id return all units in the property which are not leased
        :param user:
        :param property_id:
        :return:
        """
        with Session() as session:
            user_id = user.user_id

            _property: PropertyORM = session.query(PropertyORM).filter(
                PropertyORM.property_id == property_id).first()

            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=_property.company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access the Property")

            property_units: list[UnitORM] = session.query(UnitORM).filter(UnitORM.property_id == property_id,
                                                                          UnitORM.is_occupied == False).all()

            return [Unit(**building.to_dict()) for building in property_units
                    if building] if isinstance(property_units, list) else []

    @error_handler
    async def add_unit(self, user: User, unit_data: AddUnit, property_id: str) -> AddUnit:
        """

        :param user:
        :param property_id:
        :param unit_data:
        :return:
        """
        with Session() as session:
            user_id = user.user_id

            _property: PropertyORM = session.query(PropertyORM).filter(
                PropertyORM.property_id == property_id).first()

            is_company_member: bool = await self.is_company_member(user_id=user_id,
                                                                   company_id=_property.company_id,
                                                                   session=session)
            if not is_company_member:
                raise UnauthorizedError(description="Not Authorized to access the Property")

            # Note Adding one more unit number of units and available units
            _property.number_of_units += 1
            _property.available_units += 1

            unit: UnitORM = UnitORM(**unit_data.dict())
            session.add(unit)
            session.commit()
            return unit_data

    @error_handler
    async def get_unit(self, user: User, building_id: str, unit_id: str) -> Unit | None:
        """

        :param building_id:
        :param user:
        :param unit_id:
        :return:
        """
        with Session() as session:
            unit_data: UnitORM = session.query(UnitORM).filter(
                UnitORM.property_id == building_id, UnitORM.unit_id == unit_id).first()
            if unit_data is None:
                return None
            return Unit(**unit_data.to_dict())

    @error_handler
    async def update_unit(self, user_id: str, unit_data: Unit) -> Unit | None:
        """

        :param user_id:
        :param unit_data:
        :return:
        """
        with Session() as session:
            unit_orm: UnitORM = session.query(UnitORM).filter(UnitORM.unit_id == unit_data.unit_id,
                                                              UnitORM.property_id == unit_data.property_id).first()

            if unit_orm:
                # Update the fields in tenant_orm based on the values in tenant
                for field in unit_data.__dict__:
                    if field in unit_orm.__dict__ and unit_data.__dict__[field] is not None:
                        setattr(unit_orm, field, unit_data.__dict__[field])

                # Commit the changes to the database
                session.commit()

                return Unit(**unit_orm.to_dict())
            return None

    @error_handler
    async def create_billable_item(self, billable_item: CreateInvoicedItem) -> CreateInvoicedItem:
        """
        **create_billable_item**

        :param billable_item:
        :return:
        """
        with Session() as session:
            billable_orm: ItemsORM = ItemsORM(**billable_item.dict())
            session.add(billable_orm)
            session.commit()
            return billable_item

    @error_handler
    async def get_billed_item(self, property_id: str, item_number: str):
        with Session() as session:
            billable_orm: ItemsORM = session.query(ItemsORM).filter(ItemsORM.property_id == property_id,
                                                                    ItemsORM.item_number == item_number).first()
            return CreateInvoicedItem(**billable_orm.to_dict())

    @error_handler
    async def delete_billed_item(self, property_id: str, item_number: str):
        with Session() as session:
            billable_orm: ItemsORM = session.query(ItemsORM).filter(ItemsORM.property_id == property_id).first()
            billable_orm.deleted = True
            session.merge(billable_orm)
            session.commit()
            return CreateInvoicedItem(**billable_orm.to_dict())

    @error_handler
    async def get_billable_items(self, building_id: str) -> list[BillableItem]:
        """

        :param building_id:
        :return:
        """
        with Session() as session:
            billable_list: list[ItemsORM] = session.query(ItemsORM).filter(ItemsORM.property_id == building_id,
                                                                           ItemsORM.deleted == False).all()
            return [BillableItem(**item.to_dict()) for item in billable_list]

    @error_handler
    async def create_unit_bill_charge(self, charge_item: CreateUnitCharge) -> CreateUnitCharge:
        """

        :param charge_item:
        :return:
        """
        with Session() as session:
            charge_item_orm: UserChargesORM = UserChargesORM(**charge_item.dict())
            session.add(charge_item_orm)
            session.commit()
            return charge_item

    @error_handler
    async def delete_unit_charge(self, charge_id: str) -> CreateUnitCharge:
        """

        :return:
        """
        with Session() as session:
            charge_item_orm: UserChargesORM = session.query(UserChargesORM).filter(UserChargesORM.charge_id == charge_id).first()
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
        with Session() as session:
            charged_items = session.query(UserChargesORM).filter(UserChargesORM.property_id == building_id,
                                                                 UserChargesORM.unit_id == unit_id).all()
            return [CreateUnitCharge(**charge.to_dict()) for charge in charged_items if charge] if charged_items else []

    @error_handler
    async def get_item_by_number(self, item_number: str) -> BillableItem:
        """

        :param item_number:
        :return:
        """
        with Session() as session:
            billable_item: ItemsORM = session.query(ItemsORM).filter(ItemsORM.item_number == item_number).first()
            return BillableItem(**billable_item.to_dict())

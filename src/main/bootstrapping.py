def bootstrapper():
    from src.database.sql.address import AddressORM
    from src.database.sql.tenants import TenantORM
    from src.database.sql.user import UserORM
    from src.database.sql.companies import UserCompanyORM, CompanyORM
    from src.database.sql.properties import PropertyORM, UnitORM
    from src.database.sql.bank_account import BankAccountORM
    from src.database.sql.notifications import NotificationORM
    from src.database.sql.lease import LeaseAgreementORM, LeaseAgreementTemplate
    from src.database.sql.companies import TenantCompanyORM
    from src.database.sql.invoices import InvoiceORM
    from src.database.sql.invoices import ItemsORM
    from src.database.sql.invoices import UserChargesORM
    from src.database.sql.tenants import TenantAddressORM
    from src.database.sql.payments import PaymentORM

    AddressORM.create_if_not_table()
    TenantORM.create_if_not_table()
    UserORM.create_if_not_table()
    UserCompanyORM.create_if_not_table()
    CompanyORM.create_if_not_table()

    PropertyORM.create_if_not_table()
    UnitORM.create_if_not_table()
    BankAccountORM.create_if_not_table()
    NotificationORM.create_if_not_table()
    LeaseAgreementORM.create_if_not_table()
    LeaseAgreementTemplate.create_if_not_table()

    TenantCompanyORM.create_if_not_table()

    InvoiceORM.create_if_not_table()
    ItemsORM.create_if_not_table()
    UserChargesORM.create_if_not_table()
    TenantAddressORM.create_if_not_table()
    PaymentORM.create_if_not_table()

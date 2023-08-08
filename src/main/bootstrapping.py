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
    from src.database.sql.wallet import WalletTransactionORM
    from src.database.sql.user import ProfileORM
    from src.database.sql.subscriptions import PlansORM, SubscriptionsORM, PaymentReceiptORM

    classes_to_create = [
        AddressORM,
        TenantORM,
        UserORM,
        UserCompanyORM,
        CompanyORM,
        PropertyORM,
        UnitORM,
        BankAccountORM,
        NotificationORM,
        LeaseAgreementORM,
        LeaseAgreementTemplate,
        TenantCompanyORM,
        InvoiceORM,
        ItemsORM,
        UserChargesORM,
        TenantAddressORM,
        PaymentORM,
        WalletTransactionORM,
        ProfileORM,
        PlansORM,
        SubscriptionsORM,
        PaymentReceiptORM,
    ]

    for cls in classes_to_create:
        cls.create_if_not_table()

from flask import Flask
from src.controller.auth import UserController
from src.controller.companies import CompaniesController
from src.firewall import Firewall
from src.utils import template_folder, static_folder
from src.controller.encryptor import encryptor
from src.controller.notifications_controller import NotificationsController

firewall = Firewall()
company_controller = CompaniesController()

from src.controller.tenant import TenantController

tenant_controller = TenantController()
user_controller = UserController()
notifications_controller = NotificationsController()

from src.controller.lease_controller import LeaseController
lease_agreement_controller = LeaseController()

def bootstrapper():
    from src.database.sql.address import AddressORM
    from src.database.sql.tenants import TenantORM
    from src.database.sql.user import UserORM
    from src.database.sql.companies import UserCompanyORM, CompanyORM
    from src.database.sql.properties import PropertyORM, UnitORM
    from src.database.sql.bank_account import BankAccountORM
    from src.database.sql.notifications import NotificationORM
    from src.database.sql.lease import LeaseAgreementORM, LeaseAgreementTemplate

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


def create_app(config):
    app: Flask = Flask(__name__)

    app.template_folder = template_folder()
    app.static_folder = static_folder()
    app.config['SECRET_KEY'] = config.SECRET_KEY

    with app.app_context():
        encryptor.init_app(app=app)
        user_controller.init_app(app=app)
        firewall.init_app(app=app)

        from src.routes.home import home_route
        from src.routes.companies import companies_route
        from src.routes.buildings import buildings_route
        from src.routes.maintenance import maintenance_route
        from src.routes.reports import reports_route
        from src.routes.payments import payments_route
        from src.routes.invoices import invoices_route
        from src.routes.statements import statements_route
        from src.routes.tenants import tenants_route
        from src.cron.routes import cron_route

        from src.routes.auth import auth_route

        app.register_blueprint(home_route)
        app.register_blueprint(companies_route)
        app.register_blueprint(buildings_route)
        app.register_blueprint(maintenance_route)
        app.register_blueprint(reports_route)
        app.register_blueprint(payments_route)
        app.register_blueprint(invoices_route)
        app.register_blueprint(statements_route)
        app.register_blueprint(auth_route)
        app.register_blueprint(tenants_route)
        app.register_blueprint(cron_route)

        bootstrapper()

    return app

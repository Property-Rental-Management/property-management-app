import os

from flask import Flask

from src.emailer import SendMail

send_mail = SendMail()

from src.controller.auth import UserController
from src.controller.companies import CompaniesController
from src.firewall import Firewall
from src.utils import template_folder, static_folder, format_with_grouping, lease_formatter, format_square_meters, \
    format_payment_method
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
from src.controller.lease_controller import InvoiceManager

cache_path = os.path.join(os.getcwd(), "cache", "invoices_cache.pkl")

invoice_man = InvoiceManager(cache_path)
from src.paywall.payfast import PayFastAPI

paywall: PayFastAPI = PayFastAPI()


def create_app(config):
    app: Flask = Flask(__name__)

    app.template_folder = template_folder()
    app.static_folder = static_folder()
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['BASE_URL'] = "https://rental-manager.site"

    with app.app_context():
        encryptor.init_app(app=app)
        user_controller.init_app(app=app)
        tenant_controller.init_app(app=app)
        firewall.init_app(app=app)
        send_mail.init_app(app=app)
        invoice_man.init_app(app=app)
        paywall.init(app=app)

        from src.routes.home import home_route
        from src.routes.companies import companies_route
        from src.routes.buildings import buildings_route
        from src.routes.maintenance import maintenance_route
        from src.routes.reports import reports_route
        from src.routes.payments import payments_route
        from src.routes.invoices import invoices_route
        from src.routes.statements import statements_route
        from src.routes.tenants import tenants_route
        from src.routes.admin_notices import notices_route

        from src.cron.routes import cron_route
        from src.routes.auth import auth_route

        from src.main.bootstrapping import bootstrapper

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
        app.register_blueprint(notices_route)

        app.jinja_env.filters['currency'] = format_with_grouping
        app.jinja_env.filters['lease_counter'] = lease_formatter
        app.jinja_env.filters['square_meters'] = format_square_meters
        app.jinja_env.filters['payment_method'] = format_payment_method

        bootstrapper()

    return app
